import os
import subprocess
from PIL import Image, ImageChops # Pillow for image manipulation
import config 

def compile_latex_to_pdf(latex_filepath, output_dir):
    """Compiles a LaTeX file to PDF."""
    try:
        cmd = [
            'pdflatex',
            '-interaction=nonstopmode',
            f'-output-directory={output_dir}',
            latex_filepath
        ]
        # Run twice to ensure all cross-references are resolved
        subprocess.run(cmd, check=True, capture_output=True)
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"Compiled {os.path.basename(latex_filepath)} to PDF.")
        # Return path to generated PDF
        pdf_name = os.path.splitext(os.path.basename(latex_filepath))[0] + '.pdf'
        return os.path.join(output_dir, pdf_name)
    except subprocess.CalledProcessError as e:
        print(f"Error compiling LaTeX {latex_filepath}: {e.stderr.decode()}")
        return None
    except FileNotFoundError:
        print("pdflatex command not found. Ensure LaTeX distribution is installed and in PATH.")
        return None

def convert_pdf_to_images(pdf_filepath, output_dir, dpi=config.PDF_DPI):
    """Converts each page of a PDF to a PNG image."""
    try:
        base_name = os.path.splitext(os.path.basename(pdf_filepath))[0]
        # Using Ghostscript via command line for robust PDF to image conversion
        output_pattern = os.path.join(output_dir, f"{base_name}_page%d.png")
        cmd = [
            'gs', # Ghostscript command
            '-dNOPAUSE', '-dBATCH', '-sDEVICE=pngalpha',
            f'-r{dpi}',
            f'-sOutputFile={output_pattern}',
            pdf_filepath
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Collect paths to generated images
        image_paths = []
        i = 1
        while True:
            img_path = os.path.join(output_dir, f"{base_name}_page{i}.png")
            if os.path.exists(img_path):
                image_paths.append(img_path)
                i += 1
            else:
                break
        print(f"Converted {os.path.basename(pdf_filepath)} to {len(image_paths)} images.")
        return image_paths
    except subprocess.CalledProcessError as e:
        print(f"Error converting PDF {pdf_filepath} to images: {e.stderr.decode()}")
        return None
    except FileNotFoundError:
        print("Ghostscript (gs) command not found. Ensure it is installed and in PATH.")
        return None

def compare_images_visually(img1_path, img2_path, diff_output_path=None):
    """
    Compares two images and returns a 'difference score' (RMSE) and
    optionally saves a visual diff image.
    Lower RMSE is better (0 means identical).
    """
    try:
        img1 = Image.open(img1_path).convert('RGB')
        img2 = Image.open(img2_path).convert('RGB')

        # Ensure images are same size
        if img1.size != img2.size:
            max_width = max(img1.width, img2.width)
            max_height = max(img1.height, img2.height)
            img1 = img1.resize((max_width, max_height), Image.Resampling.LANCZOS)
            img2 = img2.resize((max_width, max_height), Image.Resampling.LANCZOS)
            print(f"Warning: Images had different sizes. Resized to {img1.size}.")

        diff = ImageChops.difference(img1, img2)
        
        # Calculate RMSE (Root Mean Square Error) as a diff score
        # Sum of squared differences per pixel, then sqrt(mean)
        stat = ImageChops.difference(img1, img2).getbbox() # For non-zero pixel check
        if stat is None: # Images are identical
            rmse = 0.0
        else:
            # Calculate root mean square error
            squared_diff = sum(c**2 for c in diff.getdata())
            rmse = (squared_diff / (img1.size[0] * img1.size[1]))**0.5

        if diff_output_path:
            # Highlight differences, e.g., using a red overlay
            diff.save(diff_output_path)

        return rmse
    except Exception as e:
        print(f"Error comparing images {img1_path} and {img2_path}: {e}")
        return None



