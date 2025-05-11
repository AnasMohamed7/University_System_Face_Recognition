// DOM Elements
const loginForm = document.getElementById('login-form');
const faceRecognition = document.getElementById('face-recognition');
const idNumberInput = document.getElementById('id-number');
const loginButton = document.getElementById('login-button');
const captureButton = document.getElementById('capture-button');
const retakeButton = document.getElementById('retake-button');
const verifyButton = document.getElementById('verify-button');
const cancelButton = document.getElementById('cancel-button');
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const capturedImage = document.getElementById('captured-image');

// Variables
let stream = null;
const API_URL = 'http://localhost:5000'; // Your Python server URL
let currentNationalId = '';

// Event Listeners
loginButton.addEventListener('click', handleLogin);
captureButton.addEventListener('click', captureImage);
retakeButton.addEventListener('click', setupCamera);
verifyButton.addEventListener('click', verifyFace);
cancelButton.addEventListener('click', cancelFaceRecognition);

// Input validation for National ID
idNumberInput.addEventListener('input', function (e) {
    // Remove any non-digit characters
    this.value = this.value.replace(/\D/g, '');

    // Limit to 14 digits
    if (this.value.length > 14) {
        this.value = this.value.slice(0, 14);
    }
});

// Function to check if all digits in a string are the same
function hasAllSameDigits(str) {
    return /^(\d)\1+$/.test(str);
}

function handleLogin() {
    const idNumber = idNumberInput.value.trim();

    // Validate National ID (must be exactly 14 digits)
    if (!/^\d{14}$/.test(idNumber)) {
        alert('الرجاء إدخال رقم قومي صحيح مكون من 14 رقم');
        return;
    }

    // Check if all digits are the same
    if (hasAllSameDigits(idNumber)) {
        alert('الرقم القومي غير صالح. لا يمكن أن تكون جميع الأرقام متطابقة.');
        return;
    }

    // Store the ID for verification later
    currentNationalId = idNumber;

    // Show face recognition
    loginForm.style.display = 'none';
    faceRecognition.style.display = 'block';

    // Setup camera
    setupCamera();
}

async function setupCamera() {
    try {
        // Reset UI
        captureButton.style.display = 'block';
        retakeButton.style.display = 'none';
        verifyButton.style.display = 'none';
        capturedImage.style.display = 'none';
        video.style.display = 'block';

        // Stop any existing stream
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }

        // Get new stream
        stream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: false
        });

        video.srcObject = stream;
    } catch (error) {
        console.error('Error accessing camera:', error);
        alert('لا يمكن الوصول إلى الكاميرا. يرجى التأكد من منح الأذونات المطلوبة.');
    }
}

function captureImage() {
    const context = canvas.getContext('2d');

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert canvas to image
    const imageDataUrl = canvas.toDataURL('image/png');
    capturedImage.src = imageDataUrl;

    // Update UI
    video.style.display = 'none';
    capturedImage.style.display = 'block';
    captureButton.style.display = 'none';
    retakeButton.style.display = 'inline-block';
    verifyButton.style.display = 'inline-block';

    // Stop camera stream
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }

    console.log('Image captured. Ready to send to face recognition API.');
}

async function verifyFace() {
    // Show loading state
    verifyButton.textContent = 'جاري التحقق...';
    verifyButton.disabled = true;

    try {
        // Get the image data from the canvas
        const imageData = canvas.toDataURL('image/png');

        // Send the image and national ID to your Python API
        const response = await fetch(`${API_URL}/recognize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image: imageData,
                nationalId: currentNationalId
            })
        });

        const result = await response.json();

        if (result.success) {
            alert(`مرحباً بك، ${result.user}!`);
            // Redirect to dashboard or home page
            // window.location.href = 'dashboard.html';
        } else {
            alert(result.message);
            cancelFaceRecognition(); // Go back to login form
        }
    } catch (error) {
        console.error('Error:', error);
        alert('حدث خطأ أثناء التحقق من الوجه. يرجى المحاولة مرة أخرى.');
        cancelFaceRecognition();
    } finally {
        // Reset button
        verifyButton.textContent = 'تحقق';
        verifyButton.disabled = false;
    }
}

function cancelFaceRecognition() {
    // Stop camera stream
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }

    // Show login form again
    faceRecognition.style.display = 'none';
    loginForm.style.display = 'block';
}