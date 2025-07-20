// Enhanced Canvas Chat Functionality
class CanvasChat {
  constructor() {
    this.canvasId = window.canvasData.canvasId
    this.currentUser = window.canvasData.currentUser
    this.messages = []
    this.isOpen = false
    this.unreadCount = 0

    this.init()
  }

  init() {
    this.chatPanel = document.getElementById("chat-panel")
    this.chatMessages = document.getElementById("chat-messages")
    this.messageInput = document.getElementById("message-input")
    this.sendButton = document.getElementById("send-message")
    this.toggleButton = document.getElementById("toggle-chat")
    this.chatToggleBtn = document.getElementById("chat-toggle-btn")
    this.chatBadge = document.getElementById("chat-badge")

    this.setupEventListeners()
    this.loadMessages()

    // Poll for new messages every 5 seconds
    setInterval(() => {
      this.loadMessages()
    }, 5000)

    console.log("Canvas Chat initialized")
  }

  setupEventListeners() {
    // Send message
    this.sendButton.addEventListener("click", () => {
      this.sendMessage()
    })

    this.messageInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault()
        this.sendMessage()
      }
    })

    // Toggle chat panel
    this.toggleButton.addEventListener("click", () => {
      this.toggleChat()
    })

    this.chatToggleBtn.addEventListener("click", () => {
      this.toggleChat()
    })

    // Auto-resize message input
    this.messageInput.addEventListener("input", () => {
      this.messageInput.style.height = "auto"
      this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 100) + "px"
    })
  }

  toggleChat() {
    this.isOpen = !this.isOpen

    if (this.isOpen) {
      this.chatPanel.classList.add("open")
      this.chatToggleBtn.style.display = "none"
      this.unreadCount = 0
      this.updateBadge()
      this.scrollToBottom()
      this.messageInput.focus()
    } else {
      this.chatPanel.classList.remove("open")
      this.chatToggleBtn.style.display = "flex"
    }
  }

  async sendMessage() {
    const message = this.messageInput.value.trim()
    if (!message) return

    try {
      const response = await fetch(`/canvas/api/canvas/${this.canvasId}/chat/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: message,
          message_type: "text",
        }),
      })

      const result = await response.json()

      if (result.success) {
        this.messageInput.value = ""
        this.messageInput.style.height = "auto"
        this.addMessage(result.message)
        this.scrollToBottom()
      } else {
        console.error("Failed to send message:", result.message)
        alert("Failed to send message: " + result.message)
      }
    } catch (error) {
      console.error("Error sending message:", error)
      alert("Error sending message: " + error.message)
    }
  }

  async loadMessages() {
    try {
      const response = await fetch(`/canvas/api/canvas/${this.canvasId}/chat/messages`)
      const result = await response.json()

      if (result.success) {
        const newMessages = result.messages.filter((msg) => !this.messages.find((existing) => existing.id === msg.id))

        newMessages.forEach((message) => {
          this.addMessage(message)

          // Count unread messages from other users
          if (message.user_id !== this.currentUser.id && !this.isOpen) {
            this.unreadCount++
          }
        })

        this.updateBadge()

        if (newMessages.length > 0 && this.isOpen) {
          this.scrollToBottom()
        }
      }
    } catch (error) {
      console.error("Error loading messages:", error)
    }
  }

  addMessage(messageData) {
    // Check if message already exists
    if (this.messages.find((msg) => msg.id === messageData.id)) {
      return
    }

    this.messages.push(messageData)

    const messageElement = this.createMessageElement(messageData)
    this.chatMessages.appendChild(messageElement)

    // Animate message appearance
    messageElement.style.opacity = "0"
    messageElement.style.transform = "translateY(20px)"

    requestAnimationFrame(() => {
      messageElement.style.transition = "all 0.3s ease"
      messageElement.style.opacity = "1"
      messageElement.style.transform = "translateY(0)"
    })
  }

  createMessageElement(messageData) {
    const messageDiv = document.createElement("div")
    messageDiv.className = `chat-message ${messageData.user_id === this.currentUser.id ? "own" : "other"}`

    const headerDiv = document.createElement("div")
    headerDiv.className = "message-header"

    const authorSpan = document.createElement("span")
    authorSpan.className = "message-author"
    authorSpan.textContent = messageData.user_name || "Unknown User"

    const timeSpan = document.createElement("span")
    timeSpan.className = "message-time"
    timeSpan.textContent = this.formatTime(messageData.created_at)

    headerDiv.appendChild(authorSpan)
    headerDiv.appendChild(timeSpan)

    const contentDiv = document.createElement("div")
    contentDiv.className = "message-content"

    if (messageData.message_type === "text") {
      contentDiv.textContent = messageData.message
    } else if (messageData.message_type === "file") {
      const link = document.createElement("a")
      link.href = messageData.file_path
      link.target = "_blank"
      link.innerHTML = `<i class="fas fa-file"></i> ${messageData.message}`
      contentDiv.appendChild(link)
    }

    messageDiv.appendChild(headerDiv)
    messageDiv.appendChild(contentDiv)

    return messageDiv
  }

  formatTime(timestamp) {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now - date

    if (diff < 60000) {
      // Less than 1 minute
      return "Just now"
    } else if (diff < 3600000) {
      // Less than 1 hour
      const minutes = Math.floor(diff / 60000)
      return `${minutes}m ago`
    } else if (diff < 86400000) {
      // Less than 1 day
      const hours = Math.floor(diff / 3600000)
      return `${hours}h ago`
    } else {
      return date.toLocaleDateString()
    }
  }

  updateBadge() {
    if (this.unreadCount > 0) {
      this.chatBadge.textContent = this.unreadCount > 99 ? "99+" : this.unreadCount
      this.chatBadge.style.display = "flex"
    } else {
      this.chatBadge.style.display = "none"
    }
  }

  scrollToBottom() {
    requestAnimationFrame(() => {
      this.chatMessages.scrollTop = this.chatMessages.scrollHeight
    })
  }
}

// Initialize chat when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  window.canvasChat = new CanvasChat()
})
