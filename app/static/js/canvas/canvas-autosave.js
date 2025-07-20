// Enhanced Canvas Auto-save Functionality
class CanvasAutoSave {
  constructor() {
    this.canvasId = window.canvasData.canvasId
    this.saveTimeout = null
    this.saveDelay = 2000 // 2 seconds
    this.isSaving = false
    this.lastSaved = new Date()
    this.isDirty = false

    this.init()
  }

  init() {
    this.statusIndicator = document.getElementById("save-status")
    this.statusText = document.getElementById("save-text")

    // Update status every 30 seconds
    setInterval(() => {
      this.updateStatus()
    }, 30000)

    // Auto-save on page unload
    window.addEventListener("beforeunload", () => {
      if (this.isDirty) {
        this.performSave(true)
      }
    })

    console.log("Canvas Auto-save initialized")
  }

  markDirty() {
    this.isDirty = true
    this.save()
  }

  save() {
    // Clear existing timeout
    if (this.saveTimeout) {
      clearTimeout(this.saveTimeout)
    }

    // Set new timeout
    this.saveTimeout = setTimeout(() => {
      this.performSave()
    }, this.saveDelay)

    // Update UI to show pending save
    this.updateStatus("pending")
  }

  async performSave(immediate = false) {
    if (this.isSaving && !immediate) return

    this.isSaving = true
    this.updateStatus("saving")

    try {
      const canvasData = this.getCanvasData()

      const response = await fetch(`/canvas/api/canvas/${this.canvasId}/save`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          content: canvasData,
        }),
      })

      const result = await response.json()

      if (result.success) {
        this.lastSaved = new Date(result.last_saved || new Date())
        this.isDirty = false
        this.updateStatus("saved")
        console.log("Canvas auto-saved successfully")
      } else {
        this.updateStatus("error")
        console.error("Auto-save failed:", result.message)
      }
    } catch (error) {
      this.updateStatus("error")
      console.error("Auto-save error:", error)
    } finally {
      this.isSaving = false
    }
  }

  getCanvasData() {
    const elements = []

    if (window.canvasCore && window.canvasCore.elements) {
      window.canvasCore.elements.forEach((data, id) => {
        elements.push({
          id: id,
          type: data.type,
          x: data.x,
          y: data.y,
          width: data.width,
          height: data.height,
          content: data.content,
          style: data.style,
          zIndex: data.zIndex || 1,
        })
      })
    }

    return {
      elements: elements,
      settings: {
        theme: document.documentElement.dataset.theme || "light",
        zoom: window.canvasCore ? window.canvasCore.zoom : 1,
      },
    }
  }

  updateStatus(status) {
    if (!this.statusIndicator || !this.statusText) return

    const indicator = this.statusIndicator.parentElement

    // Remove all status classes
    indicator.classList.remove("saving", "error")

    switch (status) {
      case "pending":
        this.statusText.textContent = "Saving..."
        indicator.classList.add("saving")
        break

      case "saving":
        this.statusText.textContent = "Saving..."
        indicator.classList.add("saving")
        break

      case "saved":
        this.statusText.textContent = "Saved"
        break

      case "error":
        this.statusText.textContent = "Save failed"
        indicator.classList.add("error")
        break

      default:
        // Show time since last save
        const now = new Date()
        const diff = Math.floor((now - this.lastSaved) / 1000)

        if (diff < 60) {
          this.statusText.textContent = "Saved"
        } else if (diff < 3600) {
          const minutes = Math.floor(diff / 60)
          this.statusText.textContent = `Saved ${minutes}m ago`
        } else {
          const hours = Math.floor(diff / 3600)
          this.statusText.textContent = `Saved ${hours}h ago`
        }
        break
    }
  }

  // Force save (for manual save button)
  forceSave() {
    if (this.saveTimeout) {
      clearTimeout(this.saveTimeout)
    }
    this.performSave(true)
  }
}

// Initialize auto-save when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  window.canvasAutoSave = new CanvasAutoSave()

  // Hook into canvas core to trigger auto-save
  if (window.canvasCore) {
    const originalAutoSave = window.canvasCore.autoSave
    window.canvasCore.autoSave = () => {
      window.canvasAutoSave.markDirty()
    }
  }
})
