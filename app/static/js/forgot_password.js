const forgotForm = document.getElementById("forgotForm");
const messageBox = document.getElementById("messageBox");

forgotForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("forgotUsername").value;
  const forgot_key = document.getElementById("forgotKey").value;
  const new_password = document.getElementById("newPassword").value;
  const confirm_password = document.getElementById("confirmPassword").value;

  // Password confirmation check
  if (new_password !== confirm_password) {
    showMessage("❌ Passwords do not match", false);
    return;
  }

  try {
    const res = await fetch("/api/forgot-password", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken(),
      },
      body: JSON.stringify({ username, forgot_key, new_password }),
    });

    const data = await res.json();

    if (data.status === "success") {
      showMessage(data.message, true);
      // Redirect to home after 1.5 seconds
      setTimeout(() => {
        window.location.href = "/";
      }, 1500);
    } else {
      showMessage(data.message || "❌ Error occurred", false);
    }
  } catch (error) {
    showMessage("Network error", false);
  }
});

function showMessage(msg, success) {
  messageBox.textContent = msg;
  messageBox.className = success ? "mt-4 text-green-600" : "mt-4 text-red-600";
}

function getCSRFToken() {
  let cookieValue = null;
  const cookies = document.cookie.split(";");
  for (let cookie of cookies) {
    cookie = cookie.trim();
    if (cookie.startsWith("csrftoken=")) {
      cookieValue = cookie.substring("csrftoken=".length);
      break;
    }
  }
  return cookieValue;
}
