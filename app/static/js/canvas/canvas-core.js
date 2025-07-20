// Enhanced Canvas Core - Figma-like functionality
class CanvasCore {
  constructor() {
    this.canvasId = window.canvasData.canvasId
    this.currentUser = window.canvasData.currentUser
    this.elements = new Map()
    this.selectedElements = new Set()
    this.currentTool = "select"
    this.zoom = 1
    this.pan = { x: 0, y: 0 }
    this.isDragging = false
    this.isPanning = false
    this.dragStart = { x: 0, y: 0 }
    this.panStart = { x: 0, y: 0 }
    this.clipboard = null
    this.history = []
    this.historyIndex = -1
    this.maxHistory = 50
    this.virtualSize = 5000
    this.gridVisible = true
    this.snapToGrid = true
    this.gridSize = 20
    this.snapThreshold = 8
    this.isCreatingElement = false
    this.tempElement = null
    this.marqueeBox = null
    this.marqueeStart = null
    this.activeTool = "move"
    this.init()
  }

  init() {
    this.workspace = document.getElementById("canvas-workspace")
    this.elementsContainer = document.getElementById("canvas-elements")
    this.propertiesPanel = document.getElementById("properties-panel")
    this.propertiesContent = document.getElementById("properties-content")
    this.fileUpload = document.getElementById("file-upload")
    // Set workspace size
    this.workspace.style.width = this.virtualSize + "px"
    this.workspace.style.height = this.virtualSize + "px"
    this.gridCanvas = document.createElement("canvas")
    this.gridCanvas.id = "dynamic-grid-canvas"
    this.gridCanvas.style.position = "absolute"
    this.gridCanvas.style.top = "0"
    this.gridCanvas.style.left = "0"
    this.gridCanvas.style.pointerEvents = "none"
    this.gridCanvas.style.zIndex = "0"
    this.workspace.insertBefore(this.gridCanvas, this.workspace.firstChild)
    this.updateGrid()
    this.setupEventListeners()
    this.setupKeyboardShortcuts()
    this.setupFileUpload()
    this.loadCanvas()
    this.saveToHistory()
    this.setupContextMenu()
    this.updateTransform()
    // Add grid toggle button if not present
    if (!document.getElementById("grid-toggle")) {
      const gridBtn = document.createElement("button")
      gridBtn.className = "tool-btn"
      gridBtn.id = "grid-toggle"
      gridBtn.title = "Toggle Grid"
      gridBtn.innerHTML = '<i class="fas fa-border-all"></i>'
      document.querySelector(".canvas-toolbar .toolbar-group:last-child").appendChild(gridBtn)
      gridBtn.addEventListener("click", () => {
        this.gridVisible = !this.gridVisible
        this.updateGrid()
      })
    }
    // Add Save button if not present
    if (!document.getElementById("save-btn")) {
      const saveBtn = document.createElement("button")
      saveBtn.className = "tool-btn btn-primary"
      saveBtn.id = "save-btn"
      saveBtn.title = "Save Canvas"
      saveBtn.innerHTML = '<i class="fas fa-save"></i> Save'
      document
        .querySelector(".canvas-toolbar .toolbar-group:last-child")
        .insertBefore(saveBtn, document.getElementById("zoom-in"))
      saveBtn.addEventListener("click", () => this.manualSave())
    }
    // Save button in sidebar
    const saveBtn = document.getElementById("save-btn")
    if (saveBtn) {
      saveBtn.addEventListener("click", () => this.manualSave())
    }
    // Auto-save on exit
    window.addEventListener("beforeunload", (e) => {
      this.autoSave(true)
    })
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") {
        this.autoSave(true)
      }
    })
    // Ctrl+S shortcut
    document.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
        e.preventDefault()
        this.manualSave()
      }
    })
    // Initial status
    this.updateSaveStatus("saved")

    // Sidebar expand/collapse
    const sidebar = document.getElementById("figma-sidebar")
    const toggleBtn = document.getElementById("sidebar-toggle-btn")
    if (sidebar && toggleBtn) {
      // Restore state
      const collapsed = localStorage.getItem("sidebarCollapsed") === "true"
      if (collapsed) sidebar.classList.add("collapsed")
      toggleBtn.addEventListener("click", () => {
        sidebar.classList.toggle("collapsed")
        const isCollapsed = sidebar.classList.contains("collapsed")
        toggleBtn.querySelector("i").className = isCollapsed ? "fas fa-angle-double-right" : "fas fa-angle-double-left"
        localStorage.setItem("sidebarCollapsed", isCollapsed)
      })
      // Set initial icon
      toggleBtn.querySelector("i").className = collapsed ? "fas fa-angle-double-right" : "fas fa-angle-double-left"
    }
    // Render team avatars
    const avatarsDiv = document.getElementById("team-avatars")
    if (avatarsDiv && window.canvasData && window.canvasData.teamMembers) {
      avatarsDiv.innerHTML = ""
      window.canvasData.teamMembers.forEach((member) => {
        const avatar = document.createElement("div")
        avatar.className = "avatar"
        avatar.style.backgroundImage = `url('${member.avatar || "/static/images/default-avatar.png"}')`
        avatar.setAttribute("data-name", member.name)
        avatar.style.position = "relative"
        // Status dot
        const status = document.createElement("span")
        status.className = "avatar-status " + (member.status || "offline")
        avatar.appendChild(status)
        avatarsDiv.appendChild(avatar)
      })
    }
    // Dark mode toggle
    const themeBtn = document.getElementById("theme-toggle")
    if (themeBtn) {
      const html = document.documentElement
      // Restore theme
      const savedTheme = localStorage.getItem("theme")
      if (savedTheme) html.setAttribute("data-theme", savedTheme)
      themeBtn.addEventListener("click", () => {
        const current = html.getAttribute("data-theme") || "light"
        const next = current === "light" ? "dark" : "light"
        html.setAttribute("data-theme", next)
        localStorage.setItem("theme", next)
        themeBtn.querySelector("i").className = next === "dark" ? "fas fa-sun" : "fas fa-moon"
      })
      // Set initial icon
      themeBtn.querySelector("i").className = html.getAttribute("data-theme") === "dark" ? "fas fa-sun" : "fas fa-moon"
    }
    // Right panel drag/resize placeholder
    const rightPanel = document.getElementById("right-panel")
    if (rightPanel) {
      let isResizing = false
      rightPanel.addEventListener("mousedown", (e) => {
        if (e.offsetX < 8) {
          isResizing = true
          document.body.style.cursor = "ew-resize"
        }
      })
      document.addEventListener("mousemove", (e) => {
        if (isResizing) {
          const winWidth = window.innerWidth
          const newWidth = winWidth - e.clientX
          if (newWidth > 200 && newWidth < 480) {
            rightPanel.style.width = newWidth + "px"
          }
        }
      })
      document.addEventListener("mouseup", () => {
        if (isResizing) {
          isResizing = false
          document.body.style.cursor = ""
        }
      })
    }
    // Keyboard shortcut overlay
    const shortcutOverlay = document.getElementById("shortcut-overlay")
    const shortcutClose = document.getElementById("shortcut-close")
    const showShortcuts = () => {
      shortcutOverlay.style.display = "flex"
    }
    const hideShortcuts = () => {
      shortcutOverlay.style.display = "none"
    }
    document.addEventListener("keydown", (e) => {
      if ((e.key === "?" && !e.shiftKey && !e.ctrlKey && !e.metaKey) || e.key === "F1") {
        e.preventDefault()
        showShortcuts()
      }
      if (e.key === "Escape") {
        hideShortcuts()
      }
    })
    if (shortcutClose) shortcutClose.addEventListener("click", hideShortcuts)
    shortcutOverlay.addEventListener("click", (e) => {
      if (e.target === shortcutOverlay) hideShortcuts()
    })
    // Multi-selection & marquee
    this.workspace.addEventListener("mousedown", (e) => {
      if (e.target === this.workspace && (this.activeTool === "move" || this.activeTool === "hand")) {
        this.marqueeStart = { x: e.clientX, y: e.clientY }
        this.marqueeBox = document.createElement("div")
        this.marqueeBox.className = "selection-box"
        this.marqueeBox.style.left = `${e.clientX}px`
        this.marqueeBox.style.top = `${e.clientY}px`
        this.marqueeBox.style.width = "0px"
        this.marqueeBox.style.height = "0px"
        document.body.appendChild(this.marqueeBox)
      }
    })
    document.addEventListener("mousemove", (e) => {
      if (this.marqueeBox && this.marqueeStart) {
        const x1 = this.marqueeStart.x
        const y1 = this.marqueeStart.y
        const x2 = e.clientX
        const y2 = e.clientY
        const left = Math.min(x1, x2)
        const top = Math.min(y1, y2)
        const width = Math.abs(x2 - x1)
        const height = Math.abs(y2 - y1)
        this.marqueeBox.style.left = `${left}px`
        this.marqueeBox.style.top = `${top}px`
        this.marqueeBox.style.width = `${width}px`
        this.marqueeBox.style.height = `${height}px`
        // Highlight elements in marquee
        this.highlightElementsInMarquee(left, top, width, height, e)
      }
    })
    document.addEventListener("mouseup", (e) => {
      if (this.marqueeBox) {
        this.marqueeBox.remove()
        this.marqueeBox = null
        this.marqueeStart = null
      }
    })

    console.log("Canvas Core initialized")
  }

  setupEventListeners() {
    // Tool selection
    document.querySelectorAll(".tool-btn[data-tool]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const tool = e.currentTarget.dataset.tool
        this.setTool(tool)
      })
    })

    // Canvas interactions
    this.workspace.addEventListener("mousedown", this.handleMouseDown.bind(this))
    this.workspace.addEventListener("mousemove", this.handleMouseMove.bind(this))
    this.workspace.addEventListener("mouseup", this.handleMouseUp.bind(this))
    // Remove any duplicate click handlers
    this.workspace.onclick = null
    this.workspace.addEventListener("click", this.handleCanvasClick.bind(this))

    // Pan with middle mouse or Ctrl+drag
    this.workspace.addEventListener("mousedown", (e) => {
      if (e.button === 1 || (e.ctrlKey && e.button === 0)) {
        this.isPanning = true
        this.panStart = { x: e.clientX, y: e.clientY }
        this.panOrigin = { ...this.pan }
        e.preventDefault()
      }
    })
    document.addEventListener("mousemove", (e) => {
      if (this.isPanning) {
        const dx = e.clientX - this.panStart.x
        const dy = e.clientY - this.panStart.y
        this.pan.x = this.clampPan(this.panOrigin.x + dx, "x")
        this.pan.y = this.clampPan(this.panOrigin.y + dy, "y")
        this.updateTransform()
      }
    })
    document.addEventListener("mouseup", () => {
      if (this.isPanning) {
        this.isPanning = false
      }
    })
    // Keyboard panning
    document.addEventListener("keydown", (e) => {
      if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key)) {
        const step = 50 / this.zoom
        if (e.key === "ArrowLeft") this.pan.x = this.clampPan(this.pan.x + step, "x")
        if (e.key === "ArrowRight") this.pan.x = this.clampPan(this.pan.x - step, "x")
        if (e.key === "ArrowUp") this.pan.y = this.clampPan(this.pan.y + step, "y")
        if (e.key === "ArrowDown") this.pan.y = this.clampPan(this.pan.y - step, "y")
        this.updateTransform()
      }
    })
    // Touch pan (framework ready)
    let lastTouch = null
    this.workspace.addEventListener("touchstart", (e) => {
      if (e.touches.length === 1) {
        lastTouch = { x: e.touches[0].clientX, y: e.touches[0].clientY }
      }
    })
    this.workspace.addEventListener("touchmove", (e) => {
      if (e.touches.length === 1 && lastTouch) {
        const dx = e.touches[0].clientX - lastTouch.x
        const dy = e.touches[0].clientY - lastTouch.y
        this.pan.x = this.clampPan(this.pan.x + dx, "x")
        this.pan.y = this.clampPan(this.pan.y + dy, "y")
        this.updateTransform()
        lastTouch = { x: e.touches[0].clientX, y: e.touches[0].clientY }
      }
    })
    this.workspace.addEventListener("touchend", () => {
      lastTouch = null
    })
    // Mouse wheel zoom (Ctrl+scroll)
    this.workspace.addEventListener(
      "wheel",
      (e) => {
        if (e.ctrlKey) {
          e.preventDefault()
          const prevZoom = this.zoom
          if (e.deltaY < 0) this.zoomIn(e, true)
          else this.zoomOut(e, true)
          // Zoom to mouse
          const rect = this.workspace.getBoundingClientRect()
          const mouseX = e.clientX - rect.left
          const mouseY = e.clientY - rect.top
          const wx = (mouseX - this.pan.x) / prevZoom
          const wy = (mouseY - this.pan.y) / prevZoom
          this.pan.x = mouseX - wx * this.zoom
          this.pan.y = mouseY - wy * this.zoom
          this.pan.x = this.clampPan(this.pan.x, "x")
          this.pan.y = this.clampPan(this.pan.y, "y")
          this.updateTransform()
        }
      },
      { passive: false },
    )
    // Zoom controls
    document.getElementById("zoom-in").addEventListener("click", () => this.zoomIn())
    document.getElementById("zoom-out").addEventListener("click", () => this.zoomOut())
    // Zoom to fit
    if (!document.getElementById("zoom-fit")) {
      const fitBtn = document.createElement("button")
      fitBtn.className = "tool-btn"
      fitBtn.id = "zoom-fit"
      fitBtn.title = "Zoom to Fit"
      fitBtn.innerHTML = '<i class="fas fa-expand"></i>'
      document.querySelector(".canvas-toolbar .toolbar-group:last-child").appendChild(fitBtn)
      fitBtn.addEventListener("click", () => this.zoomToFit())
    }
    // Reset view
    if (!document.getElementById("zoom-reset")) {
      const resetBtn = document.createElement("button")
      resetBtn.className = "tool-btn"
      resetBtn.id = "zoom-reset"
      resetBtn.title = "Reset View"
      resetBtn.innerHTML = '<i class="fas fa-home"></i>'
      document.querySelector(".canvas-toolbar .toolbar-group:last-child").appendChild(resetBtn)
      resetBtn.addEventListener("click", () => this.resetView())
    }
    // Prevent context menu on canvas
    this.workspace.addEventListener("contextmenu", (e) => {
      e.preventDefault()
      this.showContextMenu(e.clientX, e.clientY)
    })

    // Undo/Redo
    document.getElementById("undo-btn").addEventListener("click", () => this.undo())
    document.getElementById("redo-btn").addEventListener("click", () => this.redo())

    // Save
    document.getElementById("save-btn").addEventListener("click", () => this.saveCanvas())

    // Context menu
    this.workspace.addEventListener("contextmenu", (e) => {
      e.preventDefault()
      this.showContextMenu(e.clientX, e.clientY)
    })

    // Hide context menu on click
    document.addEventListener("click", () => {
      document.getElementById("context-menu").style.display = "none"
    })

    // Context menu actions
    document.getElementById("context-menu").addEventListener("click", (e) => {
      const action = e.target.closest(".context-item")?.dataset.action
      if (action) {
        this.handleContextAction(action)
      }
    })

    // Drag and drop
    this.setupDragAndDrop()

    console.log("Event listeners setup complete")
  }

  setupKeyboardShortcuts() {
    document.addEventListener("keydown", (e) => {
      // Prevent shortcuts when typing in inputs
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") {
        return
      }

      if (e.ctrlKey || e.metaKey) {
        switch (e.key.toLowerCase()) {
          case "z":
            e.preventDefault()
            if (e.shiftKey) {
              this.redo()
            } else {
              this.undo()
            }
            break
          case "y":
            e.preventDefault()
            this.redo()
            break
          case "c":
            e.preventDefault()
            this.copySelected()
            break
          case "v":
            e.preventDefault()
            this.paste()
            break
          case "a":
            e.preventDefault()
            this.selectAll()
            break
          case "s":
            e.preventDefault()
            this.saveCanvas()
            break
          case "=":
          case "+":
            e.preventDefault()
            this.zoomIn()
            break
          case "-":
            e.preventDefault()
            this.zoomOut()
            break
          case "0":
            e.preventDefault()
            this.resetZoom()
            break
        }
      } else {
        // Tool shortcuts
        switch (e.key.toLowerCase()) {
          case "v":
            this.setTool("select")
            break
          case "t":
            this.setTool("text")
            break
          case "s":
            this.setTool("shape")
            break
          case "i":
            this.setTool("image")
            break
          case "d":
            this.setTool("document")
            break
          case "delete":
          case "backspace":
            e.preventDefault()
            this.deleteSelected()
            break
          case "escape":
            this.clearSelection()
            this.setTool("select")
            break
        }
      }
    })
  }

  setupFileUpload() {
    this.fileUpload.addEventListener("change", (e) => {
      const files = Array.from(e.target.files)
      if (files.length > 0) {
        this.handleFileUpload(files)
      }
      e.target.value = "" // Reset file input
    })
  }

  setupDragAndDrop() {
    this.workspace.addEventListener("dragover", (e) => {
      e.preventDefault()
      this.workspace.classList.add("drag-over")
    })

    this.workspace.addEventListener("dragleave", (e) => {
      if (!this.workspace.contains(e.relatedTarget)) {
        this.workspace.classList.remove("drag-over")
      }
    })

    this.workspace.addEventListener("drop", (e) => {
      e.preventDefault()
      this.workspace.classList.remove("drag-over")

      const files = Array.from(e.dataTransfer.files)
      if (files.length > 0) {
        const rect = this.workspace.getBoundingClientRect()
        const x = (e.clientX - rect.left) / this.zoom
        const y = (e.clientY - rect.top) / this.zoom

        this.handleFileUpload(files, { x, y })
      }
    })
  }

  setTool(tool) {
    console.log("Setting tool to:", tool)
    this.currentTool = tool

    // Update UI
    document.querySelectorAll(".tool-btn").forEach((btn) => {
      btn.classList.remove("active")
    })
    document.querySelector(`[data-tool="${tool}"]`)?.classList.add("active")

    // Update cursor
    this.updateCursor()

    // Handle special tools
    if (tool === "shape") {
      this.showShapeModal()
    } else if (tool === "image" || tool === "document") {
      this.fileUpload.click()
    }
  }

  updateCursor() {
    const cursors = {
      select: "default",
      text: "text",
      shape: "crosshair",
      image: "crosshair",
      document: "crosshair",
    }

    this.workspace.style.cursor = cursors[this.currentTool] || "default"
  }

  handleMouseDown(e) {
    if (e.target === this.workspace || e.target === this.elementsContainer) {
      this.isDragging = true
      this.dragStart = { x: e.clientX, y: e.clientY }

      if (this.currentTool === "select") {
        this.startSelection(e)
      }
    }
  }

  handleMouseMove(e) {
    if (this.isDragging && this.currentTool === "select") {
      this.updateSelection(e)
    }
  }

  handleMouseUp(e) {
    if (this.isDragging) {
      this.isDragging = false
      this.endSelection()
    }
  }

  handleCanvasClick(e) {
    if (e.target === this.workspace || e.target === this.elementsContainer) {
      const rect = this.workspace.getBoundingClientRect()
      const x = (e.clientX - rect.left) / this.zoom
      const y = (e.clientY - rect.top) / this.zoom

      console.log("Canvas clicked at:", x, y, "Tool:", this.currentTool)

      switch (this.currentTool) {
        case "text":
          this.createTextElement(x, y)
          break
        case "image":
          this.fileUpload.click()
          break
        case "document":
          this.fileUpload.click()
          break
        case "select":
          this.clearSelection()
          break
      }
    }
  }

  createTextElement(x, y) {
    console.log("Creating text element at:", x, y)

    const element = {
      id: this.generateId(),
      type: "text",
      x: x,
      y: y,
      width: 200,
      height: 50,
      content: "Double click to edit",
      style: {
        fontSize: "16px",
        fontFamily: "Arial, sans-serif",
        color: "#333333",
        textAlign: "left",
        fontWeight: "normal",
      },
      zIndex: this.getNextZIndex(),
    }

    this.addElement(element)
    this.saveToHistory()
    this.setTool("select")
  }

  createShapeElement(x, y, shapeType) {
    console.log("Creating shape element:", shapeType, "at:", x, y)

    const shapes = {
      rectangle: { width: 150, height: 100 },
      circle: { width: 100, height: 100 },
      triangle: { width: 100, height: 87 },
      diamond: { width: 100, height: 100 },
      arrow: { width: 120, height: 60 },
      line: { width: 150, height: 2 },
    }

    const shapeConfig = shapes[shapeType] || shapes.rectangle

    const element = {
      id: this.generateId(),
      type: "shape",
      x: x,
      y: y,
      width: shapeConfig.width,
      height: shapeConfig.height,
      content: { shapeType: shapeType },
      style: {
        backgroundColor: this.getShapeColor(shapeType),
        borderRadius: shapeType === "circle" ? "50%" : "4px",
      },
      zIndex: this.getNextZIndex(),
    }

    this.addElement(element)
    this.saveToHistory()
  }

  getShapeColor(shapeType) {
    const colors = {
      rectangle: "#007bff",
      circle: "#28a745",
      triangle: "#ffc107",
      diamond: "#dc3545",
      arrow: "#6f42c1",
      line: "#17a2b8",
    }
    return colors[shapeType] || "#007bff"
  }

  async handleFileUpload(files, position = null) {
    console.log("Handling file upload:", files.length, "files")

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      const formData = new FormData()
      formData.append("file", file)

      try {
        const response = await fetch(`/canvas/api/canvas/${this.canvasId}/upload`, {
          method: "POST",
          body: formData,
        })

        const data = await response.json()

        if (data.success) {
          const x = position ? position.x + i * 20 : this.workspace.offsetWidth / 2 / this.zoom
          const y = position ? position.y + i * 20 : this.workspace.offsetHeight / 2 / this.zoom

          if (file.type.startsWith("image/")) {
            this.createImageElement(x, y, data.url, file.name)
          } else {
            this.createDocumentElement(x, y, data.file)
          }
        } else {
          console.error("Upload failed:", data.message)
          alert("Upload failed: " + data.message)
        }
      } catch (error) {
        console.error("Upload error:", error)
        alert("Upload failed: " + error.message)
      }
    }

    this.setTool("select")
  }

  createImageElement(x, y, src, alt) {
    console.log("Creating image element at:", x, y)

    const element = {
      id: this.generateId(),
      type: "image",
      x: x,
      y: y,
      width: 200,
      height: 150,
      content: { src: src, alt: alt },
      style: {},
      zIndex: this.getNextZIndex(),
    }

    this.addElement(element)
    this.saveToHistory()
  }

  createDocumentElement(x, y, fileData) {
    console.log("Creating document element at:", x, y)

    const element = {
      id: this.generateId(),
      type: "document",
      x: x,
      y: y,
      width: 200,
      height: 120,
      content: {
        fileName: fileData.original_filename,
        fileType: fileData.file_type,
        fileSize: fileData.file_size,
        url: `/static/uploads/canvas/${fileData.filename}`,
      },
      style: {},
      zIndex: this.getNextZIndex(),
    }

    this.addElement(element)
    this.saveToHistory()
  }

  addElement(elementData) {
    console.log("Adding element:", elementData)

    const element = this.createElement(elementData)
    this.elements.set(elementData.id, elementData)
    this.elementsContainer.appendChild(element)

    // Auto-save
    this.autoSave()
  }

  createElement(data) {
    const element = document.createElement("div")
    element.className = "canvas-element"
    element.dataset.elementId = data.id
    element.style.left = data.x + "px"
    element.style.top = data.y + "px"
    element.style.width = data.width + "px"
    element.style.height = data.height + "px"
    element.style.zIndex = data.zIndex || 1

    // Add content based on type
    switch (data.type) {
      case "text":
        this.createTextContent(element, data)
        break
      case "shape":
        this.createShapeContent(element, data)
        break
      case "image":
        this.createImageContent(element, data)
        break
      case "document":
        this.createDocumentContent(element, data)
        break
    }

    // Add event listeners
    this.addElementEventListeners(element)

    return element
  }

  createTextContent(element, data) {
    const textArea = document.createElement("textarea")
    textArea.className = "text-element"
    textArea.value = data.content
    textArea.style.fontSize = data.style.fontSize || "16px"
    textArea.style.fontFamily = data.style.fontFamily || "Arial, sans-serif"
    textArea.style.color = data.style.color || "#333333"
    textArea.style.textAlign = data.style.textAlign || "left"
    textArea.style.fontWeight = data.style.fontWeight || "normal"

    textArea.addEventListener("input", () => {
      data.content = textArea.value
      this.autoSave()
    })

    textArea.addEventListener("dblclick", (e) => {
      e.stopPropagation()
      textArea.focus()
      textArea.select()
    })

    element.appendChild(textArea)
  }

  createShapeContent(element, data) {
    element.className += ` shape-element shape-${data.content.shapeType}`
    element.style.backgroundColor = data.style.backgroundColor
    element.style.borderRadius = data.style.borderRadius
  }

  createImageContent(element, data) {
    const img = document.createElement("img")
    img.src = data.content.src
    img.alt = data.content.alt || "Canvas Image"
    img.style.width = "100%"
    img.style.height = "100%"
    img.style.objectFit = "cover"
    img.style.borderRadius = "4px"
    img.draggable = false

    element.className += " image-element"
    element.appendChild(img)
  }

  createDocumentContent(element, data) {
    element.className += " document-element"

    const icon = document.createElement("div")
    icon.className = "document-icon"
    icon.innerHTML = this.getDocumentIcon(data.content.fileType)

    const name = document.createElement("div")
    name.className = "document-name"
    name.textContent = data.content.fileName

    const size = document.createElement("div")
    size.className = "document-size"
    size.textContent = this.formatFileSize(data.content.fileSize)

    element.appendChild(icon)
    element.appendChild(name)
    element.appendChild(size)

    // Add click handler to open document
    element.addEventListener("click", (e) => {
      if (this.currentTool === "select" && !this.isDragging) {
        window.open(data.content.url, "_blank")
      }
    })
  }

  getDocumentIcon(fileType) {
    const icons = {
      pdf: '<i class="fas fa-file-pdf"></i>',
      doc: '<i class="fas fa-file-word"></i>',
      docx: '<i class="fas fa-file-word"></i>',
      xls: '<i class="fas fa-file-excel"></i>',
      xlsx: '<i class="fas fa-file-excel"></i>',
      ppt: '<i class="fas fa-file-powerpoint"></i>',
      pptx: '<i class="fas fa-file-powerpoint"></i>',
      txt: '<i class="fas fa-file-alt"></i>',
    }
    return icons[fileType] || '<i class="fas fa-file"></i>'
  }

  formatFileSize(bytes) {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  addElementEventListeners(element) {
    let isDragging = false
    let dragStart = { x: 0, y: 0 }
    let elementStart = { x: 0, y: 0 }

    element.addEventListener("mousedown", (e) => {
      e.stopPropagation()

      if (this.currentTool === "select") {
        isDragging = true
        dragStart = { x: e.clientX, y: e.clientY }
        elementStart = {
          x: Number.parseInt(element.style.left),
          y: Number.parseInt(element.style.top),
        }

        this.selectElement(element)
      }
    })

    const handleMouseMove = (e) => {
      if (isDragging && this.currentTool === "select") {
        const dx = (e.clientX - dragStart.x) / this.zoom
        const dy = (e.clientY - dragStart.y) / this.zoom

        const newX = elementStart.x + dx
        const newY = elementStart.y + dy

        element.style.left = newX + "px"
        element.style.top = newY + "px"

        // Update data
        const elementData = this.elements.get(element.dataset.elementId)
        elementData.x = newX
        elementData.y = newY
      }
    }

    const handleMouseUp = () => {
      if (isDragging) {
        isDragging = false
        this.autoSave()
        this.saveToHistory()
        document.removeEventListener("mousemove", handleMouseMove)
        document.removeEventListener("mouseup", handleMouseUp)
      }
    }

    document.addEventListener("mousemove", handleMouseMove)
    document.addEventListener("mouseup", handleMouseUp)

    element.addEventListener("click", (e) => {
      e.stopPropagation()
      if (this.currentTool === "select") {
        this.selectElement(element)
      }
    })
  }

  selectElement(element) {
    // Clear previous selection if not holding Ctrl/Cmd
    if (!event.ctrlKey && !event.metaKey) {
      this.clearSelection()
    }

    // Select new element
    element.classList.add("selected")
    this.selectedElements.add(element.dataset.elementId)

    // Update properties panel
    this.updatePropertiesPanel()
  }

  clearSelection() {
    document.querySelectorAll(".canvas-element.selected").forEach((el) => {
      el.classList.remove("selected")
    })
    this.selectedElements.clear()
    this.updatePropertiesPanel()
  }

  updatePropertiesPanel() {
    if (this.selectedElements.size === 0) {
      this.propertiesContent.innerHTML = '<p class="text-muted">Select an element to edit properties</p>'
      return
    }

    if (this.selectedElements.size === 1) {
      const elementId = Array.from(this.selectedElements)[0]
      const elementData = this.elements.get(elementId)
      this.showElementProperties(elementData)
    } else {
      this.propertiesContent.innerHTML = `<p class="text-muted">${this.selectedElements.size} elements selected</p>`
    }
  }

  showElementProperties(elementData) {
    let html = `
            <div class="property-group">
                <label class="property-label">Position</label>
                <div class="row">
                    <div class="col-6">
                        <input type="number" class="property-input" data-property="x" value="${Math.round(elementData.x)}" placeholder="X">
                    </div>
                    <div class="col-6">
                        <input type="number" class="property-input" data-property="y" value="${Math.round(elementData.y)}" placeholder="Y">
                    </div>
                </div>
            </div>
            <div class="property-group">
                <label class="property-label">Size</label>
                <div class="row">
                    <div class="col-6">
                        <input type="number" class="property-input" data-property="width" value="${Math.round(elementData.width)}" placeholder="Width">
                    </div>
                    <div class="col-6">
                        <input type="number" class="property-input" data-property="height" value="${Math.round(elementData.height)}" placeholder="Height">
                    </div>
                </div>
            </div>
        `

    // Type-specific properties
    if (elementData.type === "text") {
      html += `
                <div class="property-group">
                    <label class="property-label">Font Size</label>
                    <input type="number" class="property-input" data-property="fontSize" value="${Number.parseInt(elementData.style.fontSize)}" min="8" max="72">
                </div>
                <div class="property-group">
                    <label class="property-label">Font Family</label>
                    <select class="property-input" data-property="fontFamily">
                        <option value="Arial, sans-serif" ${elementData.style.fontFamily === "Arial, sans-serif" ? "selected" : ""}>Arial</option>
                        <option value="Georgia, serif" ${elementData.style.fontFamily === "Georgia, serif" ? "selected" : ""}>Georgia</option>
                        <option value="'Times New Roman', serif" ${elementData.style.fontFamily === "'Times New Roman', serif" ? "selected" : ""}>Times New Roman</option>
                        <option value="'Courier New', monospace" ${elementData.style.fontFamily === "'Courier New', monospace" ? "selected" : ""}>Courier New</option>
                    </select>
                </div>
                <div class="property-group">
                    <label class="property-label">Text Color</label>
                    <input type="color" class="property-input" data-property="color" value="${elementData.style.color}">
                </div>
            `
    } else if (elementData.type === "shape") {
      html += `
                <div class="property-group">
                    <label class="property-label">Background Color</label>
                    <input type="color" class="property-input" data-property="backgroundColor" value="${elementData.style.backgroundColor}">
                </div>
            `
    }

    this.propertiesContent.innerHTML = html

    // Add event listeners to property inputs
    this.propertiesContent.querySelectorAll(".property-input").forEach((input) => {
      input.addEventListener("input", (e) => {
        this.updateElementProperty(elementData, e.target.dataset.property, e.target.value)
      })
    })
  }

  updateElementProperty(elementData, property, value) {
    const element = document.querySelector(`[data-element-id="${elementData.id}"]`)
    if (!element) return

    // Update data
    if (["x", "y", "width", "height"].includes(property)) {
      elementData[property] = Number.parseFloat(value)
      element.style[property === "x" ? "left" : property === "y" ? "top" : property] = value + "px"
    } else if (property === "fontSize") {
      elementData.style.fontSize = value + "px"
      const textElement = element.querySelector(".text-element")
      if (textElement) {
        textElement.style.fontSize = value + "px"
      }
    } else if (property === "fontFamily") {
      elementData.style.fontFamily = value
      const textElement = element.querySelector(".text-element")
      if (textElement) {
        textElement.style.fontFamily = value
      }
    } else if (property === "color") {
      elementData.style.color = value
      const textElement = element.querySelector(".text-element")
      if (textElement) {
        textElement.style.color = value
      }
    } else if (property === "backgroundColor") {
      elementData.style.backgroundColor = value
      element.style.backgroundColor = value
    }

    this.autoSave()
  }

  // Zoom functionality
  zoomIn() {
    this.zoom = Math.min(this.zoom * 1.2, 5)
    this.updateZoom()
  }

  zoomOut() {
    this.zoom = Math.max(this.zoom / 1.2, 0.1)
    this.updateZoom()
  }

  resetZoom() {
    this.zoom = 1
    this.updateZoom()
  }

  zoomToFit() {
    if (this.elements.size === 0) {
      this.resetZoom()
      return
    }

    // Calculate bounds of all elements
    let minX = Number.POSITIVE_INFINITY,
      minY = Number.POSITIVE_INFINITY,
      maxX = Number.NEGATIVE_INFINITY,
      maxY = Number.NEGATIVE_INFINITY

    this.elements.forEach((element) => {
      minX = Math.min(minX, element.x)
      minY = Math.min(minY, element.y)
      maxX = Math.max(maxX, element.x + element.width)
      maxY = Math.max(maxY, element.y + element.height)
    })

    const padding = 50
    const contentWidth = maxX - minX + padding * 2
    const contentHeight = maxY - minY + padding * 2

    const scaleX = this.workspace.offsetWidth / contentWidth
    const scaleY = this.workspace.offsetHeight / contentHeight

    this.zoom = Math.min(scaleX, scaleY, 1)
    this.updateZoom()
  }

  updateZoom() {
    this.elementsContainer.style.transform = `scale(${this.zoom})`
    document.getElementById("zoom-level").textContent = Math.round(this.zoom * 100) + "%"
  }

  // History management
  saveToHistory() {
    const state = this.getCanvasState()

    // Remove any states after current index
    this.history = this.history.slice(0, this.historyIndex + 1)

    // Add new state
    this.history.push(JSON.stringify(state))
    this.historyIndex++

    // Limit history size
    if (this.history.length > this.maxHistory) {
      this.history.shift()
      this.historyIndex--
    }
  }

  undo() {
    if (this.historyIndex > 0) {
      this.historyIndex--
      const state = JSON.parse(this.history[this.historyIndex])
      this.restoreCanvasState(state)
    }
  }

  redo() {
    if (this.historyIndex < this.history.length - 1) {
      this.historyIndex++
      const state = JSON.parse(this.history[this.historyIndex])
      this.restoreCanvasState(state)
    }
  }

  getCanvasState() {
    const elements = []
    this.elements.forEach((data, id) => {
      elements.push({ ...data })
    })
    return { elements }
  }

  restoreCanvasState(state) {
    // Clear current elements
    this.elementsContainer.innerHTML = ""
    this.elements.clear()
    this.clearSelection()

    // Restore elements
    state.elements.forEach((elementData) => {
      this.addElement(elementData)
    })
  }

  // Context menu
  showContextMenu(x, y) {
    const contextMenu = document.getElementById("context-menu")
    contextMenu.style.display = "block"
    contextMenu.style.left = x + "px"
    contextMenu.style.top = y + "px"
  }

  handleContextAction(action) {
    switch (action) {
      case "copy":
        this.copySelected()
        break
      case "paste":
        this.paste()
        break
      case "delete":
        this.deleteSelected()
        break
      case "duplicate":
        this.duplicateSelected()
        break
      case "bring-front":
        this.bringToFront()
        break
      case "send-back":
        this.sendToBack()
        break
    }
  }

  copySelected() {
    if (this.selectedElements.size > 0) {
      const selectedData = []
      this.selectedElements.forEach((id) => {
        selectedData.push({ ...this.elements.get(id) })
      })
      this.clipboard = selectedData
      console.log("Copied", selectedData.length, "elements")
    }
  }

  paste() {
    if (this.clipboard) {
      this.clearSelection()
      this.clipboard.forEach((data) => {
        const newData = { ...data }
        newData.id = this.generateId()
        newData.x += 20
        newData.y += 20
        newData.zIndex = this.getNextZIndex()
        this.addElement(newData)

        // Select pasted element
        const element = document.querySelector(`[data-element-id="${newData.id}"]`)
        if (element) {
          element.classList.add("selected")
          this.selectedElements.add(newData.id)
        }
      })
      this.saveToHistory()
      this.updatePropertiesPanel()
    }
  }

  deleteSelected() {
    if (this.selectedElements.size > 0) {
      this.selectedElements.forEach((id) => {
        const element = document.querySelector(`[data-element-id="${id}"]`)
        if (element) {
          element.remove()
        }
        this.elements.delete(id)
      })
      this.clearSelection()
      this.autoSave()
      this.saveToHistory()
    }
  }

  duplicateSelected() {
    this.copySelected()
    this.paste()
  }

  bringToFront() {
    const maxZ = this.getNextZIndex()
    this.selectedElements.forEach((id) => {
      const element = document.querySelector(`[data-element-id="${id}"]`)
      const data = this.elements.get(id)
      if (element && data) {
        data.zIndex = maxZ
        element.style.zIndex = maxZ
      }
    })
    this.autoSave()
  }

  sendToBack() {
    this.selectedElements.forEach((id) => {
      const element = document.querySelector(`[data-element-id="${id}"]`)
      const data = this.elements.get(id)
      if (element && data) {
        data.zIndex = 1
        element.style.zIndex = 1
      }
    })
    this.autoSave()
  }

  selectAll() {
    this.clearSelection()
    document.querySelectorAll(".canvas-element").forEach((element) => {
      element.classList.add("selected")
      this.selectedElements.add(element.dataset.elementId)
    })
    this.updatePropertiesPanel()
  }

  // Shape modal
  showShapeModal() {
    const modal = new bootstrap.Modal(document.getElementById("shapeModal"))
    modal.show()

    // Add event listeners to shape items
    document.querySelectorAll(".shape-item").forEach((item) => {
      item.addEventListener("click", (e) => {
        const shapeType = e.currentTarget.dataset.shape
        modal.hide()

        // Create shape at center of viewport
        const x = this.workspace.offsetWidth / 2 / this.zoom
        const y = this.workspace.offsetHeight / 2 / this.zoom

        this.createShapeElement(x, y, shapeType)
        this.setTool("select")
      })
    })
  }

  // Load canvas data
  async loadCanvas() {
    try {
      const response = await fetch(`/canvas/api/canvas/${this.canvasId}/load`)
      const data = await response.json()
      if (data.success && data.content && data.content.elements) {
        this.restoreCanvasState(data.content)
        console.log("Canvas loaded with", data.content.elements.length, "elements")
      }
    } catch (error) {
      console.error("Failed to load canvas:", error)
    }
  }

  // Save canvas data
  async saveCanvas() {
    try {
      const canvasData = this.getCanvasState()

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
        this.updateSaveStatus("saved")
        console.log("Canvas saved successfully")
      } else {
        this.updateSaveStatus("error")
        console.error("Save failed:", result.message)
      }
    } catch (error) {
      this.updateSaveStatus("error")
      console.error("Save error:", error)
    }
  }

  autoSave() {
    // Debounced auto-save
    clearTimeout(this.autoSaveTimeout)
    this.autoSaveTimeout = setTimeout(() => {
      this.saveCanvas()
    }, 2000)
  }

  updateSaveStatus(status) {
    const indicator = document.getElementById("save-indicator")
    const statusIcon = document.getElementById("save-status")
    const statusText = document.getElementById("save-text")

    if (!indicator || !statusIcon || !statusText) return

    indicator.classList.remove("saving", "error")

    switch (status) {
      case "saving":
        indicator.classList.add("saving")
        statusText.textContent = "Saving..."
        break
      case "saved":
        statusText.textContent = "Saved"
        break
      case "error":
        indicator.classList.add("error")
        statusText.textContent = "Save failed"
        break
    }
  }

  // Utility functions
  generateId() {
    return "element_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9)
  }

  generateId() {
    return "element_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9)
  }

  getNextZIndex() {
    let maxZ = 0
    this.elements.forEach((element) => {
      maxZ = Math.max(maxZ, element.zIndex || 1)
    })
    return maxZ + 1
  }

  // Selection box functionality
  startSelection(e) {
    this.selectionBox = document.createElement("div")
    this.selectionBox.className = "selection-box"
    this.selectionBox.style.left = e.clientX + "px"
    this.selectionBox.style.top = e.clientY + "px"
    this.selectionBox.style.width = "0px"
    this.selectionBox.style.height = "0px"
    document.body.appendChild(this.selectionBox)

    this.selectionStart = { x: e.clientX, y: e.clientY }
  }

  updateSelection(e) {
    if (!this.selectionBox) return

    const left = Math.min(this.selectionStart.x, e.clientX)
    const top = Math.min(this.selectionStart.y, e.clientY)
    const width = Math.abs(e.clientX - this.selectionStart.x)
    const height = Math.abs(e.clientY - this.selectionStart.y)

    this.selectionBox.style.left = left + "px"
    this.selectionBox.style.top = top + "px"
    this.selectionBox.style.width = width + "px"
    this.selectionBox.style.height = height + "px"

    // Highlight elements within selection
    this.highlightElementsInSelection(left, top, width, height)
  }

  endSelection() {
    if (this.selectionBox) {
      this.selectionBox.remove()
      this.selectionBox = null
    }
    this.updatePropertiesPanel()
  }

  highlightElementsInSelection(left, top, width, height) {
    const selectionRect = { left, top, right: left + width, bottom: top + height }

    document.querySelectorAll(".canvas-element").forEach((element) => {
      const elementRect = element.getBoundingClientRect()

      if (this.rectsIntersect(selectionRect, elementRect)) {
        element.classList.add("selected")
        this.selectedElements.add(element.dataset.elementId)
      } else if (!event.ctrlKey && !event.metaKey) {
        element.classList.remove("selected")
        this.selectedElements.delete(element.dataset.elementId)
      }
    })
  }

  rectsIntersect(rect1, rect2) {
    return !(
      rect1.right < rect2.left ||
      rect1.left > rect2.right ||
      rect1.bottom < rect2.top ||
      rect1.top > rect2.bottom
    )
  }
}

// --- Real-time collaboration with Socket.IO ---
const socket = io()
socket.emit("join_canvas", { canvas_id: window.canvasData.canvasId })

function sendCanvasUpdate(update) {
  socket.emit("canvas_update", {
    canvas_id: window.canvasData.canvasId,
    update,
  })
}

socket.on("canvas_update", (data) => {
  if (typeof applyCanvasUpdate === "function") {
    applyCanvasUpdate(data.update)
  }
})

// Apply a full canvas update from another user
function applyCanvasUpdate(update) {
  if (update.type === "full" && update.state) {
    // Prevent echo: only update if state is different
    if (JSON.stringify(window.canvasCore.getCanvasState()) !== JSON.stringify(update.state)) {
      window.canvasCore.restoreCanvasState(update.state)
    }
  }
}

// Patch element add/edit/delete to emit updates
const origAddElement = window.CanvasCore.prototype.addElement
window.CanvasCore.prototype.addElement = function (elementData) {
  origAddElement.call(this, elementData)
  sendCanvasUpdate({ type: "full", state: this.getCanvasState() })
}

const origUpdateElementProperty = window.CanvasCore.prototype.updateElementProperty
window.CanvasCore.prototype.updateElementProperty = function (element, property, value) {
  const elementData = this.elements.get(element.dataset.elementId)
  origUpdateElementProperty.call(this, element, property, value)
  sendCanvasUpdate({ type: "full", state: this.getCanvasState() })
}

const origDeleteSelected = window.CanvasCore.prototype.deleteSelected
window.CanvasCore.prototype.deleteSelected = function () {
  origDeleteSelected.call(this)
  sendCanvasUpdate({ type: "full", state: this.getCanvasState() })
}

// Initialize canvas when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM loaded, initializing canvas...")
  window.canvasCore = new CanvasCore()
  // Permission-aware UI
  const perms = window.canvasData.userPermissions || []
  if (!perms.includes("write")) {
    // Hide or disable edit/delete controls
    document
      .querySelectorAll(
        '.tool-btn[data-tool="text"], .tool-btn[data-tool="shape"], .tool-btn[data-tool="image"], .tool-btn[data-tool="document"], .tool-btn#undo-btn, .tool-btn#redo-btn',
      )
      .forEach((btn) => {
        btn.disabled = true
        btn.title = "View-only access"
      })
    // Prevent element creation/edit/delete
    if (window.canvasCore) {
      window.canvasCore.setTool = () => {
        alert("You have view-only access.")
      }
      window.canvasCore.createTextElement = () => {
        alert("You have view-only access.")
      }
      window.canvasCore.createShapeElement = () => {
        alert("You have view-only access.")
      }
      window.canvasCore.createImageElement = () => {
        alert("You have view-only access.")
      }
      window.canvasCore.createDocumentElement = () => {
        alert("You have view-only access.")
      }
      window.canvasCore.deleteSelected = () => {
        alert("You have view-only access.")
      }
    }
  }

  // Initialize file upload handler
  const fileUpload = document.getElementById("file-upload")
  if (fileUpload) {
    fileUpload.addEventListener("change", (e) => {
      if (window.canvasCore) {
        window.canvasCore.handleFileUpload(Array.from(e.target.files))
      }
    })
  }

  console.log("Canvas initialization complete")
})
