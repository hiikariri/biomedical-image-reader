import os
import imageio.v3 as iio
import matplotlib.pyplot as plt
import pydicom
from pydicom.pixel_data_handlers.util import apply_modality_lut
import numpy as np
import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox as messagebox
from matplotlib.widgets import Slider


def adjust_brightness_contrast(image, brightness=1.0, contrast=1.0):
    image = image.astype(np.float32)
    mean = np.mean(image)

    image = (image - mean) * contrast + mean
    image = image * brightness
    image = np.clip(image, 0, 255)
    return image.astype(np.uint8)


def normalize_pixel_data(image):
    min_val = np.min(image)
    max_val = np.max(image)

    if max_val > min_val:
        normalized_image = (image - min_val) / (max_val - min_val) * 255.0
    else:
        normalized_image = np.zeros_like(image)

    return normalized_image.astype(np.uint8)


def plot_histogram(image, ax_hist):
    ax_hist.clear()
    ax_hist.set_title('Histogram')

    if len(image.shape) == 2:
        ax_hist.hist(image.ravel(), bins=256, range=(
            0, 255), color='gray', alpha=0.7)
    else:
        for i, color in enumerate(['red', 'green', 'blue']):
            ax_hist.hist(image[..., i].ravel(), bins=256,
                         range=(0, 255), color=color, alpha=0.7)

    ax_hist.set_xlim([0, 255])
    ax_hist.set_ylim([0, None])
    ax_hist.set_xlabel('Pixel Intensity')
    ax_hist.set_ylabel('Frequency')


def show_image(image_path):
    img = iio.imread(image_path)
    img = img.astype(np.float32)
    img = normalize_pixel_data(img)

    fig, (ax, ax_hist) = plt.subplots(2, 1, figsize=(8, 6))
    plt.subplots_adjust(left=0.25, bottom=0.25)

    img_display = ax.imshow(img, cmap='gray' if len(img.shape) == 2 else None)
    ax.axis('off')

    plot_histogram(img, ax_hist)

    ax_brightness = plt.axes([0.25, 0.15, 0.65, 0.03],
                             facecolor='lightgoldenrodyellow')
    ax_contrast = plt.axes([0.25, 0.1, 0.65, 0.03],
                           facecolor='lightgoldenrodyellow')

    slider_brightness = Slider(
        ax_brightness, 'Brightness', 0.1, 2.0, valinit=1.0)
    slider_contrast = Slider(ax_contrast, 'Contrast', 0.5, 2.0, valinit=1.0)

    def update(val):
        brightness = slider_brightness.val
        contrast = slider_contrast.val
        adjusted_img = adjust_brightness_contrast(img, brightness, contrast)
        img_display.set_data(adjusted_img)
        plot_histogram(adjusted_img, ax_hist)
        fig.canvas.draw_idle()

    slider_brightness.on_changed(update)
    slider_contrast.on_changed(update)

    plt.show()


def display_metadata(fig, dicom_data):
    metadata_text = (f"Patient Name: {getattr(dicom_data, 'PatientName', 'N/A')}\n"
                     f"Patient ID: {getattr(dicom_data, 'PatientID', 'N/A')}\n"
                     f"Patient Sex: {getattr(dicom_data, 'PatientSex', 'N/A')}\n"
                     f"Patient Birthdate: {getattr(dicom_data, 'PatientBirthDate', 'N/A')}\n"
                     f"Modality: {getattr(dicom_data, 'Modality', 'N/A')}\n"
                     f"Study Date: {getattr(dicom_data, 'StudyDate', 'N/A')}\n"
                     f"Study Description: {getattr(dicom_data, 'StudyDescription', 'N/A')}\n"
                     f"Series Number: {getattr(dicom_data, 'SeriesNumber', 'N/A')}\n"
                     f"Slice Thickness: {getattr(dicom_data, 'SliceThickness', 'N/A')}\n"
                     f"Pixel Spacing: {getattr(dicom_data, 'PixelSpacing', 'N/A')}\n"
                     f"Manufacturer: {getattr(dicom_data, 'Manufacturer', 'N/A')}\n"
                     f"Body Part Examined: {getattr(dicom_data, 'BodyPartExamined', 'N/A')}")

    fig.text(0.02, 0.95, metadata_text, va='top', fontsize=10,
             color='white', bbox=dict(facecolor='black', alpha=0.5))


def show_dicom_image_with_slider(dicom_path):
    try:
        dicom_data = pydicom.dcmread(dicom_path)
        image = apply_modality_lut(dicom_data.pixel_array, dicom_data)
        image = normalize_pixel_data(image)

        fig, (ax, ax_hist) = plt.subplots(
            2, 1, figsize=(10, 8))
        plt.subplots_adjust(left=0.25, bottom=0.35)

        img_display = ax.imshow(image, cmap=plt.cm.gray)
        ax.axis('off')
        plot_histogram(image, ax_hist)
        display_metadata(fig, dicom_data)

        ax_brightness = plt.axes(
            [0.25, 0.15, 0.65, 0.03], facecolor='lightgoldenrodyellow')
        ax_contrast = plt.axes([0.25, 0.1, 0.65, 0.03],
                               facecolor='lightgoldenrodyellow')

        slider_brightness = Slider(
            ax_brightness, 'Brightness', 0.1, 2.0, valinit=1.0)
        slider_contrast = Slider(
            ax_contrast, 'Contrast', 0.5, 2.0, valinit=1.0)

        def update(val):
            brightness = slider_brightness.val
            contrast = slider_contrast.val
            adjusted_img = adjust_brightness_contrast(
                image, brightness, contrast)
            img_display.set_data(adjusted_img)
            plot_histogram(adjusted_img, ax_hist)
            fig.canvas.draw_idle()

        slider_brightness.on_changed(update)
        slider_contrast.on_changed(update)

        plt.show()

    except FileNotFoundError:
        print("DICOM file not found.")
    except Exception as e:
        print(f"Error: {e}")
        print("Failed to read the DICOM file.")(f"Error: {e}")
        print("Failed to read the DICOM file.")


def load_dicom_series(directory):
    dicom_files = [os.path.join(directory, f)
                   for f in os.listdir(directory) if f.endswith('.dcm')]
    dicom_files.sort()
    dicom_data = [pydicom.dcmread(f) for f in dicom_files]
    return dicom_data


def show_dicom_series_with_slider(directory):
    try:
        dicom_series = load_dicom_series(directory)
        image_stack = np.array(
            [apply_modality_lut(d.pixel_array, d) for d in dicom_series])
        image_stack = normalize_pixel_data(image_stack)

        fig, (ax, ax_hist) = plt.subplots(
            2, 1, figsize=(10, 8))
        plt.subplots_adjust(left=0.25, bottom=0.35)

        slice_idx = image_stack.shape[0] // 2
        img_display = ax.imshow(image_stack[slice_idx], cmap=plt.cm.gray)
        ax.set_title(f"Slice {slice_idx}")
        ax.axis('off')

        plot_histogram(image_stack[slice_idx], ax_hist)
        display_metadata(fig, dicom_series[slice_idx])

        ax_slider = plt.axes([0.25, 0.2, 0.65, 0.03],
                             facecolor="lightgoldenrodyellow")
        slider_slice = Slider(
            ax_slider, 'Slice', 0, image_stack.shape[0] - 1, valinit=slice_idx, valstep=1)

        ax_brightness = plt.axes(
            [0.25, 0.15, 0.65, 0.03], facecolor='lightgoldenrodyellow')
        ax_contrast = plt.axes([0.25, 0.1, 0.65, 0.03],
                               facecolor='lightgoldenrodyellow')

        slider_brightness = Slider(
            ax_brightness, 'Brightness', 0.1, 2.0, valinit=1.0)
        slider_contrast = Slider(
            ax_contrast, 'Contrast', 0.5, 2.0, valinit=1.0)

        def update(val):
            slice_idx = int(slider_slice.val)
            brightness = slider_brightness.val
            contrast = slider_contrast.val

            adjusted_image = adjust_brightness_contrast(
                image_stack[slice_idx], brightness, contrast)
            img_display.set_data(adjusted_image)
            ax.set_title(f"Slice {slice_idx}")
            plot_histogram(adjusted_image, ax_hist)

            display_metadata(fig, dicom_series[slice_idx])
            fig.canvas.draw_idle()

        slider_slice.on_changed(update)
        slider_brightness.on_changed(update)
        slider_contrast.on_changed(update)

        plt.show()

    except Exception as e:
        print(f"Error loading DICOM series: {e}")


def select_file_or_directory():
    root = tk.Tk()
    root.withdraw()

    choice = messagebox.askquestion(
        "Select Option", "Would you like to select a series of DICOM (directory)?")

    if choice == 'yes':
        dir_path = filedialog.askdirectory(
            title="Select a directory with DICOM files")
        return dir_path, 'directory'
    else:
        file_path = filedialog.askopenfilename(title="Select a DICOM file or an image file",
                                               filetypes=[("DICOM files", "*.dcm"),
                                                          ("Image files",
                                                           "*.png;*.jpg;*.jpeg"),
                                                          ("All files", "*.*")])
        return file_path, 'file'


def display_selected_image():
    path, selection_type = select_file_or_directory()
    if selection_type == 'directory':
        if path:
            print(
                f"Displaying DICOM series from directory: {os.path.basename(path)}")
            show_dicom_series_with_slider(path)
        else:
            print("No directory selected.")
    elif selection_type == 'file':
        if path:
            print(f"Displaying DICOM file: {os.path.basename(path)}" if path.endswith(
                '.dcm') else f"Displaying image file: {os.path.basename(path)}")
            if path.endswith('.dcm'):
                show_dicom_image_with_slider(path)
            else:
                show_image(path)
        else:
            print("No file selected.")


if __name__ == "__main__":
    display_selected_image()
