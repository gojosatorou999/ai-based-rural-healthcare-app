let mealVideoStream;

// Open Camera
function openCamera() {
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            mealVideoStream = stream;
            document.getElementById('mealVideo').srcObject = stream;
            document.getElementById('mealVideo').style.display = 'block';
            document.querySelector("button[onclick='captureMealPhoto()']").style.display = 'inline-block';
        })
        .catch(err => console.error("Camera access denied", err));
}

// Capture Photo
function captureMealPhoto() {
    let video = document.getElementById('mealVideo');
    let canvas = document.getElementById('mealCanvas');
    let preview = document.getElementById('mealPreview');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    let context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    let imageData = canvas.toDataURL('image/png');
    preview.src = imageData;
    preview.style.display = 'block';

    mealVideoStream.getTracks().forEach(track => track.stop());
    document.getElementById('mealVideo').style.display = 'none';
    document.querySelector("button[onclick='captureMealPhoto()']").style.display = 'none';
}

// Upload Meal Image
function uploadMealImage() {
    let fileInput = document.getElementById('mealImageInput').files[0];
    let canvas = document.getElementById('mealCanvas');
    let dataURL = canvas.toDataURL('image/png');

    let formData = new FormData();
    formData.append('age', document.getElementById('age').value);
    formData.append('weight', document.getElementById('weight').value);
    formData.append('height', document.getElementById('height').value);

    if (fileInput) {
        formData.append('image', fileInput);
    } else {
        let blob = dataURItoBlob(dataURL);
        formData.append('image', blob, 'captured.png');
    }

    fetch('/upload_meal', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
            document.getElementById('calories').innerText = "Calories: " + data.calories + " kcal";
            document.getElementById('nutrients').innerText = "Nutrients: " + JSON.stringify(data.nutrients);
            document.getElementById('advice').innerText = "Advice: " + data.advice;
            document.getElementById('mealAnalyzedImage').src = data.image_url;
            document.getElementById('mealResult').style.display = 'block';
        })
        .catch(err => console.error('Error uploading meal image', err));
}

// Convert Data URL to Blob
function dataURItoBlob(dataURI) {
    let byteString = atob(dataURI.split(',')[1]);
    let mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
    let arrayBuffer = new Uint8Array(byteString.length);
    for (let i = 0; i < byteString.length; i++) {
        arrayBuffer[i] = byteString.charCodeAt(i);
    }
    return new Blob([arrayBuffer], { type: mimeString });
}
