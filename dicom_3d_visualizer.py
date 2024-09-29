import vtk
import itk
import os
import sys
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

dicom_directory = filedialog.askdirectory(title="Select DICOM Directory")
if not dicom_directory:
    print("No directory selected. Exiting.")
    sys.exit(1)

output_image = "coba_result.nrrd"
series_name = None

print("Start: Reading and writing images from the DICOM directory")

dirName = dicom_directory if dicom_directory else "."
print(f"Using DICOM directory: {dirName}")

PixelType = itk.ctype("signed short")
Dimension = 3

ImageType = itk.Image[PixelType, Dimension]

namesGenerator = itk.GDCMSeriesFileNames.New()
namesGenerator.SetUseSeriesDetails(True)
namesGenerator.AddSeriesRestriction("0008|0021")
namesGenerator.SetGlobalWarningDisplay(False)
namesGenerator.SetDirectory(dirName)

print("Searching for DICOM files...")
seriesUID = namesGenerator.GetSeriesUIDs()

if len(seriesUID) < 1:
    print("No DICOMs in: " + dirName)
    sys.exit(1)

print("The directory: " + dirName)
print("Contains the following DICOM Series: ")
for uid in seriesUID:
    print(uid)

seriesFound = False
for uid in seriesUID:
    seriesIdentifier = uid
    if series_name:
        seriesIdentifier = series_name
        seriesFound = True
    print("Reading: " + seriesIdentifier)
    fileNames = namesGenerator.GetFileNames(seriesIdentifier)

    print(f"Reading series: {seriesIdentifier}...")
    reader = itk.ImageSeriesReader[ImageType].New()
    dicomIO = itk.GDCMImageIO.New()
    reader.SetImageIO(dicomIO)
    reader.SetFileNames(fileNames)
    reader.ForceOrthogonalDirectionOff()

    print("Writing the 3D image...")
    writer = itk.ImageFileWriter[ImageType].New()
    outFileName = os.path.join(dirName, seriesIdentifier + ".nrrd")
    if output_image:
        outFileName = output_image
    writer.SetFileName(outFileName)
    writer.UseCompressionOn()
    writer.SetInput(reader.GetOutput())
    print("Writing: " + outFileName)
    writer.Update()
    print("3D image successfully written.")

    print("Extracting metadata...")

    def get_dicom_tag_value(dicomIO, tag):
        dictionary = dicomIO.GetMetaDataDictionary()

        if dictionary.HasKey(tag):
            return dictionary[tag]
        return "Unknown"

    patient_name = get_dicom_tag_value(dicomIO, "0010|0010")  # Patient Name
    study_date = get_dicom_tag_value(dicomIO, "0008|0020")    # Study Date
    modality = get_dicom_tag_value(dicomIO, "0008|0060")      # Modality
    manufacturer = get_dicom_tag_value(dicomIO, "0008|0070")  # Manufacturer

    metadata_text = f"Patient: {patient_name}\nDate: {study_date}\nModality: {modality}\nManufacturer: {manufacturer}"
    print(metadata_text)

    print("Now displaying the 3D image...")

    reader_vtk = vtk.vtkNrrdReader()
    reader_vtk.SetFileName(outFileName)
    reader_vtk.Update()

    volumeMapper = vtk.vtkSmartVolumeMapper()
    volumeMapper.SetInputConnection(reader_vtk.GetOutputPort())

    volumeProperty = vtk.vtkVolumeProperty()
    volumeProperty.ShadeOn()
    volumeProperty.SetInterpolationTypeToLinear()

    opacityTransferFunction = vtk.vtkPiecewiseFunction()
    opacityTransferFunction.AddPoint(0, 0.0)
    opacityTransferFunction.AddPoint(1000, 0.1)
    opacityTransferFunction.AddPoint(3000, 1.0)
    volumeProperty.SetScalarOpacity(opacityTransferFunction)

    colorTransferFunction = vtk.vtkColorTransferFunction()
    colorTransferFunction.AddRGBPoint(0, 0.0, 0.0, 0.0)      # Black
    colorTransferFunction.AddRGBPoint(500, 0.0, 1.0, 0.0)    # Green
    colorTransferFunction.AddRGBPoint(1000, 0.0, 0.5, 1.0)   # Light Blue
    colorTransferFunction.AddRGBPoint(1500, 1.0, 1.0, 0.0)   # Yellow
    colorTransferFunction.AddRGBPoint(3000, 1.0, 1.0, 1.0)   # White
    volumeProperty.SetColor(colorTransferFunction)

    volume = vtk.vtkVolume()
    volume.SetMapper(volumeMapper)
    volume.SetProperty(volumeProperty)

    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetSize(800, 600)
    renderWindow.AddRenderer(renderer)

    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)

    renderer.AddVolume(volume)
    renderer.SetBackground(0, 0, 0)

    text_actor = vtk.vtkTextActor()
    text_actor.SetInput(metadata_text)
    text_actor.GetTextProperty().SetFontSize(20)
    text_actor.GetTextProperty().SetColor(1, 1, 1)
    text_actor.SetPosition(10, 10)

    renderer.AddActor2D(text_actor)

    renderWindow.Render()
    print("Press 'q' or close the window to exit.")
    renderWindowInteractor.Start()

    if seriesFound:
        break
