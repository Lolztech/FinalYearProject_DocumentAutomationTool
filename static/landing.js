async function validatePassword() {
    const code = document.getElementById("access-code").value;
    const error = document.getElementById("password-error");
  
    const res = await fetch("/check_password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: code }),
    });
  
    const data = await res.json();
    if (data.valid) {
      window.location.href = "/chat_ui";
    } else {
      error.style.display = "block";
    }
  }
  