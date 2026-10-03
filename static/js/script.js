document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('analyzeForm');
    if (form) {
        form.addEventListener('submit', function() {
            const submitBtn = document.getElementById('submitBtn');
            const loader = document.getElementById('loader');
            
            submitBtn.disabled = true;
            loader.classList.remove('d-none');
            submitBtn.childNodes[2].textContent = ' Analyzing...';
        });
    }
});
