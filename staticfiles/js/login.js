document.getElementById('loginForm').addEventListener('submit', async e => {
  e.preventDefault();
  const username = document.getElementById('loginUsername').value;
  const password = document.getElementById('loginPassword').value;
  const messageBox = document.getElementById('messageBox');

  try {
    const res = await fetch('/api/login', {  // Make sure URL matches Django URLconf
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken(),
      },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();

    if (data.status === 'success') {
      messageBox.textContent = data.message;
      messageBox.className = 'mt-4 text-green-600';
      window.location.href = '/dashboard';
    } else {
      messageBox.textContent = data.message || 'Login failed';
      messageBox.className = 'mt-4 text-red-600';
    }
  } catch (error) {
    messageBox.textContent = 'Network error';
    messageBox.className = 'mt-4 text-red-600';
  }
});

function getCSRFToken() {
  const cookieValue = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];
  return cookieValue;
}
