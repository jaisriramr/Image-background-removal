from flask import Flask, request, jsonify
from rembg import remove
from PIL import Image
import requests
from io import BytesIO
import base64
import concurrent.futures

app = Flask(__name__)

# Function to stream and download image from a URL asynchronously
def download_image(url):
    response = requests.get(url, stream=True)  # Stream the image for efficiency
    response.raise_for_status()  # Check if request was successful
    return Image.open(BytesIO(response.content))

# API endpoint to remove background and return output as base64
@app.route('/remove-background', methods=['POST'])
def remove_background():
    try:
        # Get image URL from the request body (JSON format)
        data = request.json
        image_url = data['image_url']

        # Download the image asynchronously
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(download_image, image_url)
            image = future.result()

        # Convert image to byte stream
        img_byte_array = BytesIO()
        image.save(img_byte_array, format=image.format)
        img_byte_array = img_byte_array.getvalue()

        # Remove the background
        output_image = remove(img_byte_array)

        # Convert the result to a PIL image for further processing
        output_pil_image = Image.open(BytesIO(output_image))

        # Prepare to save the image with compression (PNG/JPEG depending on the image)
        output_byte_array = BytesIO()

        # Apply PNG compression or JPEG quality adjustment
        if output_pil_image.mode in ("RGBA", "P"):  # Image with transparency
            output_pil_image.save(output_byte_array, format="PNG", optimize=True)
        else:
            output_pil_image.save(output_byte_array, format="JPEG", quality=85)

        # Convert the compressed image to base64
        output_base64 = base64.b64encode(output_byte_array.getvalue()).decode('utf-8')

        # Return the base64-encoded image in the response
        return jsonify({"output_image_base64": output_base64})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
