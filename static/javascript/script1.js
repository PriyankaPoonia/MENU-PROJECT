
// Send email
document.getElementById('send-email-btn').addEventListener('click', function() {
    const email = document.getElementById('email').value;
    const subject = document.getElementById('subject').value;
    const message = document.getElementById('message').value;

    fetch('/send_email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject, body: message, to_email: email })
    })
    .then(response => response.json())
    .then(data => document.getElementById('email-status').innerText = data.message)
    .catch(err => document.getElementById('email-status').innerText = 'Error sending email.');
});

// Send bulk emails
document.getElementById('send-bulk-btn').addEventListener('click', function() {
    const emails = document.getElementById('bulk-emails').value.split(',');
    const subject = document.getElementById('bulk-subject').value;
    const message = document.getElementById('bulk-message').value;

    fetch('/send_bulk_email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipients: emails, subject, message, sender_email: 'YOUR_EMAIL', sender_password: 'YOUR_PASSWORD' })
    })
    .then(response => response.json())
    .then(data => document.getElementById('bulk-email-status').innerText = data.message)
    .catch(err => document.getElementById('bulk-email-status').innerText = 'Error sending bulk emails.');
});

// Get location
document.getElementById('get-location-btn').addEventListener('click', function() {
    fetch('/location')
    .then(response => response.json())
    .then(data => {
        document.getElementById('location-info').innerText = `City: ${data.city}, Country: ${data.country}`;
    })
    .catch(err => document.getElementById('location-info').innerText = 'Error fetching location.');
});

// Convert text to speech
document.getElementById('tts-btn').addEventListener('click', function() {
    const text = document.getElementById('tts-text').value;

    fetch('/text_to_speech', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
    })
    .then(response => response.blob())
    .then(blob => {
        const audioUrl = URL.createObjectURL(blob);
        document.getElementById('tts-audio').src = audioUrl;
    })
    .catch(err => alert('Error converting text to speech.'));
});

// Set volume
document.getElementById('set-volume-btn').addEventListener('click', function() {
    const level = parseFloat(document.getElementById('volume-level').value);

    fetch('/set_volume', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ level })
    })
    .then(response => response.json())
    .then(data => document.getElementById('volume-status').innerText = data.message)
    .catch(err => document.getElementById('volume-status').innerText = 'Error setting volume.');
});

// Upload image and apply filters
document.getElementById('upload-image-btn').addEventListener('click', function() {
    const fileInput = document.getElementById('image-file');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const filteredImagesDiv = document.getElementById('filtered-images');
        filteredImagesDiv.innerHTML = ''; // Clear previous images

        for (const filter in data) {
            const img = document.createElement('img');
            img.src = data[filter];
            filteredImagesDiv.appendChild(img);
        }
    })
    .catch(err => alert('Error applying filters.'));
});



document.addEventListener('DOMContentLoaded', function() {
    const captureBtn = document.getElementById('capture-btn');
    const selfieImage = document.getElementById('selfie-image');

    captureBtn.addEventListener('click', function() {
        fetch('/capture_face')
            .then(response => {
                if (response.ok) {
                    return response.blob();
                } else {
                    throw new Error('No face detected or error in capturing.');
                }
            })
            .then(blob => {
                const imageUrl = URL.createObjectURL(blob);
                selfieImage.src = imageUrl;
                selfieImage.style.display = 'block';
            })
            .catch(error => {
                alert(error.message);
            });
    });
});
