const chatbox = document.getElementById("chatbox");
const input = document.getElementById("message");

function appendMessage(text, type) {
  const div = document.createElement("div");
  div.className = `message ${type}`;
  div.innerHTML = text;
  chatbox.appendChild(div);
  chatbox.scrollTop = chatbox.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById("message");
    const button = document.querySelector("#input button");
    const loading = document.getElementById("loading"); // <-- Grab loading element
    const text = input.value.trim();
    if (!text) return;
  
    appendMessage(text ,"user" );
    input.value = "";
  
    // Disable input and button while waiting
    input.disabled = true;
    button.disabled = true;
    loading.style.display = "block"; 
  
    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ text })
      });
  
      const data = await res.json();
      appendMessage(data.response, "bot" );
      await updateTracker();
    } catch (error) {
      appendMessage("[Error communicating with server]", "bot" );
    } finally {
      // Re-enable input and button
      input.disabled = false;
      button.disabled = false;
      input.focus();
      loading.style.display = "none"; 
    }
}

async function triggerGreeting() {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: "" }),  // Empty string triggers greeting
    });
    const data = await res.json();
    const reply = data.response;
    appendMessage(reply, "bot");
    await updateTracker();
  }


async function updateTracker() {
    const res = await fetch("/progress");
    const data = await res.json();
    const tracker = document.getElementById("tracker");
  
    if (!data.schema_selected) {
      tracker.style.display = "none";
      return;
    }
  
    tracker.style.display = "block";
    tracker.innerHTML = `<strong>Progress: ${data.completed}/${data.total}</strong><hr>`;
  
    data.fields.forEach(item => {
      if (item.type === "section") {
        const section = document.createElement("div");
        section.className = "tracker-section";
        section.textContent = item.label;
        tracker.appendChild(section);
      }
  
      if (item.type === "field") {
        const div = document.createElement("div");
        div.className = `tracker-item ${item.status}`;
        div.textContent = item.name;
        tracker.appendChild(div);
      }
      
    });
}


async function goHome() {
    try {
      await fetch("/reset", { method: "POST" });
    } catch (err) {
      console.error("Reset failed:", err);
    }
    window.location.href = "/";
  }


window.addEventListener("DOMContentLoaded", async () => {
    await fetch("/reset", { method: "POST" });
  });
  
  
  window.onload = async () => {
    const input = document.getElementById("message");
    const button = document.querySelector("#input button");
    const loading = document.getElementById("loading");
  
    input.disabled = true;
    button.disabled = true;
    loading.style.display = "block";
  
    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: "" }),
      });
      const data = await res.json();
      appendMessage(data.response, "bot");
      await updateTracker();
    } catch (err) {
      appendMessage("[Error during greeting]", "bot");
    } finally {
      input.disabled = false;
      button.disabled = false;
      loading.style.display = "none";
      input.focus();
    }
  };
  
  

input.addEventListener("keypress", e => {
  if (e.key === "Enter") sendMessage();
});



document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.getElementById("theme-toggle");
    const root = document.body;
  
    // Load saved theme
    if (localStorage.getItem("theme") === "dark") {
      toggle.checked = true;
      setTheme("dark");
    }
  
    toggle.addEventListener("change", function () {
      const mode = toggle.checked ? "dark" : "light";
      localStorage.setItem("theme", mode);
      setTheme(mode);
    });
  
    function setTheme(mode) {
      root.classList.remove("light-mode", "dark-mode");
      root.classList.add(`${mode}-mode`);
  
      // Also apply to main elements if needed
      ["chatbox", "tracker", "chat-ui"].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
          el.classList.remove("light-mode", "dark-mode");
          el.classList.add(`${mode}-mode`);
        }
      });
    }
  });
  
