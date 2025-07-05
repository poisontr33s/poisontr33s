"""
Web Server
FastAPI-based interface for meta-automata system
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
        
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if self.active_connections:
            message_str = json.dumps(message)
            disconnected = []
            
            for connection in self.active_connections:
                try:
                    await connection.send_text(message_str)
                except:
                    disconnected.append(connection)
                    
            # Remove disconnected clients
            for connection in disconnected:
                self.disconnect(connection)

class WebServer:
    """
    FastAPI-based web server for system interface
    """
    
    def __init__(self, meta_automata, config_manager):
        self.meta_automata = meta_automata
        self.config_manager = config_manager
        self.app = FastAPI(title="Meta-Automata Interface", version="1.0.0")
        self.websocket_manager = WebSocketManager()
        
        # Setup routes
        self._setup_routes()
        self._setup_middleware()
        self._setup_static_files()
        
        # Server state
        self.server = None
        self.is_running = False
        
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            """Serve main interface"""
            return await self._serve_interface()
            
        @self.app.get("/api/status")
        async def get_status():
            """Get system status"""
            return await self._get_system_status()
            
        @self.app.get("/api/metrics")
        async def get_metrics():
            """Get performance metrics"""
            return await self._get_metrics()
            
        @self.app.get("/api/patterns")
        async def get_patterns():
            """Get learning patterns"""
            return await self._get_patterns()
            
        @self.app.get("/api/config")
        async def get_config():
            """Get system configuration"""
            return await self._get_config()
            
        @self.app.post("/api/config")
        async def update_config(config_data: Dict[str, Any]):
            """Update system configuration"""
            return await self._update_config(config_data)
            
        @self.app.get("/api/ai/services")
        async def get_ai_services():
            """Get AI service status"""
            return await self._get_ai_services()
            
        @self.app.post("/api/ai/query")
        async def ai_query(query_data: Dict[str, Any]):
            """Send query to AI services"""
            return await self._ai_query(query_data)
            
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await self._handle_websocket(websocket)
            
        @self.app.get("/docs", include_in_schema=False)
        async def get_docs():
            """Serve documentation directory listing"""
            return await self._serve_documentation()
            
    def _setup_middleware(self):
        """Setup middleware"""
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
    def _setup_static_files(self):
        """Setup static file serving"""
        
        # Create static directory if it doesn't exist
        static_dir = Path("static")
        static_dir.mkdir(exist_ok=True)
        
        # Mount static files
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        
    async def _serve_interface(self) -> str:
        """Serve the main interface HTML"""
        
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Meta-Automata Interface</title>
            <style>
                body {
                    font-family: 'Consolas', 'Monaco', monospace;
                    background: linear-gradient(135deg, #1a1a2e, #16213e);
                    color: #00ff88;
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                }
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 2px solid #00ff88;
                    padding-bottom: 20px;
                }
                .grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .panel {
                    background: rgba(0, 255, 136, 0.1);
                    border: 1px solid #00ff88;
                    border-radius: 8px;
                    padding: 20px;
                    backdrop-filter: blur(10px);
                }
                .panel h3 {
                    margin-top: 0;
                    color: #ffffff;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                }
                .metrics {
                    display: flex;
                    justify-content: space-between;
                    margin: 10px 0;
                }
                .metric-value {
                    color: #00ffff;
                    font-weight: bold;
                }
                .status-indicator {
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    margin-right: 8px;
                }
                .status-active { background: #00ff88; }
                .status-inactive { background: #ff4444; }
                .console {
                    background: #000;
                    border: 1px solid #00ff88;
                    border-radius: 8px;
                    padding: 15px;
                    height: 200px;
                    overflow-y: auto;
                    font-family: monospace;
                    font-size: 12px;
                }
                .controls {
                    display: flex;
                    gap: 10px;
                    margin-top: 15px;
                }
                button {
                    background: transparent;
                    border: 1px solid #00ff88;
                    color: #00ff88;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                button:hover {
                    background: #00ff88;
                    color: #000;
                }
                .neural-viz {
                    min-height: 200px;
                    border: 1px dashed #00ff88;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #666;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧠 Meta-Automata Control Interface</h1>
                    <p>Recursive AI Learning & Adaptation System</p>
                </div>
                
                <div class="grid">
                    <div class="panel">
                        <h3>🔥 System Status</h3>
                        <div class="metrics">
                            <span>Meta-Automata:</span>
                            <span><span class="status-indicator status-active"></span><span class="metric-value" id="automata-status">Active</span></span>
                        </div>
                        <div class="metrics">
                            <span>Vulkan Renderer:</span>
                            <span><span class="status-indicator" id="vulkan-indicator"></span><span class="metric-value" id="vulkan-status">Loading...</span></span>
                        </div>
                        <div class="metrics">
                            <span>AI Services:</span>
                            <span><span class="status-indicator" id="ai-indicator"></span><span class="metric-value" id="ai-count">0</span></span>
                        </div>
                        <div class="metrics">
                            <span>Learning Cycles:</span>
                            <span class="metric-value" id="learning-cycles">0</span>
                        </div>
                    </div>
                    
                    <div class="panel">
                        <h3>📊 Performance Metrics</h3>
                        <div class="metrics">
                            <span>Patterns Learned:</span>
                            <span class="metric-value" id="patterns-learned">0</span>
                        </div>
                        <div class="metrics">
                            <span>Adaptations Made:</span>
                            <span class="metric-value" id="adaptations-made">0</span>
                        </div>
                        <div class="metrics">
                            <span>Processing Speed:</span>
                            <span class="metric-value" id="processing-speed">0.0 Hz</span>
                        </div>
                        <div class="metrics">
                            <span>Prediction Accuracy:</span>
                            <span class="metric-value" id="prediction-accuracy">0.0%</span>
                        </div>
                    </div>
                    
                    <div class="panel">
                        <h3>🤖 AI Integration</h3>
                        <div id="ai-services-list">
                            <p>Loading AI services...</p>
                        </div>
                        <div class="controls">
                            <button onclick="testAI()">Test AI Query</button>
                            <button onclick="refreshServices()">Refresh</button>
                        </div>
                    </div>
                    
                    <div class="panel">
                        <h3>🧬 Neural Visualization</h3>
                        <div class="neural-viz" id="neural-viz">
                            Vulkan Neural Network Visualization
                            <br>Initializing...
                        </div>
                    </div>
                </div>
                
                <div class="panel">
                    <h3>💻 System Console</h3>
                    <div class="console" id="console">
                        <div style="color: #00ff88;">[SYSTEM] Meta-Automata Interface Initialized</div>
                        <div style="color: #00ffff;">[INFO] Connecting to backend services...</div>
                    </div>
                    <div class="controls">
                        <button onclick="clearConsole()">Clear</button>
                        <button onclick="saveLog()">Save Log</button>
                    </div>
                </div>
            </div>
            
            <script>
                let ws = null;
                let consoleElement = document.getElementById('console');
                
                function connectWebSocket() {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
                    
                    ws.onopen = function(event) {
                        logToConsole('[WS] Connected to Meta-Automata backend', '#00ff88');
                    };
                    
                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        handleWebSocketMessage(data);
                    };
                    
                    ws.onerror = function(error) {
                        logToConsole('[WS] Connection error', '#ff4444');
                    };
                    
                    ws.onclose = function(event) {
                        logToConsole('[WS] Connection closed. Reconnecting...', '#ffaa00');
                        setTimeout(connectWebSocket, 3000);
                    };
                }
                
                function handleWebSocketMessage(data) {
                    if (data.type === 'metrics') {
                        updateMetrics(data.data);
                    } else if (data.type === 'status') {
                        updateStatus(data.data);
                    } else if (data.type === 'log') {
                        logToConsole(`[${data.source}] ${data.message}`, data.color);
                    }
                }
                
                function updateMetrics(metrics) {
                    document.getElementById('patterns-learned').textContent = metrics.patterns_learned || 0;
                    document.getElementById('adaptations-made').textContent = metrics.adaptations_made || 0;
                    document.getElementById('processing-speed').textContent = (metrics.processing_speed || 0).toFixed(2) + ' Hz';
                    document.getElementById('prediction-accuracy').textContent = ((metrics.prediction_accuracy || 0) * 100).toFixed(1) + '%';
                }
                
                function updateStatus(status) {
                    document.getElementById('learning-cycles').textContent = status.learning_cycle || 0;
                    
                    if (status.vulkan_available) {
                        document.getElementById('vulkan-indicator').className = 'status-indicator status-active';
                        document.getElementById('vulkan-status').textContent = 'Active';
                    } else {
                        document.getElementById('vulkan-indicator').className = 'status-indicator status-inactive';
                        document.getElementById('vulkan-status').textContent = 'Software Mode';
                    }
                }
                
                function logToConsole(message, color = '#00ff88') {
                    const timestamp = new Date().toLocaleTimeString();
                    const div = document.createElement('div');
                    div.style.color = color;
                    div.textContent = `[${timestamp}] ${message}`;
                    consoleElement.appendChild(div);
                    consoleElement.scrollTop = consoleElement.scrollHeight;
                }
                
                function clearConsole() {
                    consoleElement.innerHTML = '';
                }
                
                function saveLog() {
                    const log = consoleElement.textContent;
                    const blob = new Blob([log], { type: 'text/plain' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `meta-automata-log-${Date.now()}.txt`;
                    a.click();
                }
                
                async function testAI() {
                    try {
                        const response = await fetch('/api/ai/query', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ 
                                prompt: 'Test query from Meta-Automata interface',
                                context: {} 
                            })
                        });
                        const result = await response.json();
                        logToConsole(`[AI] Test query response: ${result.content?.substring(0, 100)}...`, '#00ffff');
                    } catch (error) {
                        logToConsole(`[AI] Test query failed: ${error.message}`, '#ff4444');
                    }
                }
                
                async function refreshServices() {
                    try {
                        const response = await fetch('/api/ai/services');
                        const services = await response.json();
                        
                        const listElement = document.getElementById('ai-services-list');
                        listElement.innerHTML = '';
                        
                        services.forEach(service => {
                            const div = document.createElement('div');
                            div.className = 'metrics';
                            div.innerHTML = `
                                <span>${service.name}:</span>
                                <span><span class="status-indicator ${service.active ? 'status-active' : 'status-inactive'}"></span>${service.status}</span>
                            `;
                            listElement.appendChild(div);
                        });
                        
                        document.getElementById('ai-count').textContent = services.filter(s => s.active).length;
                        document.getElementById('ai-indicator').className = 
                            services.some(s => s.active) ? 'status-indicator status-active' : 'status-indicator status-inactive';
                            
                    } catch (error) {
                        logToConsole(`[ERROR] Failed to refresh services: ${error.message}`, '#ff4444');
                    }
                }
                
                // Initialize
                connectWebSocket();
                refreshServices();
                
                // Periodic updates
                setInterval(async () => {
                    try {
                        const response = await fetch('/api/metrics');
                        const metrics = await response.json();
                        updateMetrics(metrics);
                    } catch (error) {
                        // Silent fail for metrics updates
                    }
                }, 2000);
            </script>
        </body>
        </html>
        """
        
    async def _serve_documentation(self) -> HTMLResponse:
        """Serve documentation listing that preserves original structure"""
        
        docs_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Meta-Automata Documentation</title>
            <style>
                body { font-family: monospace; background: #1a1a2e; color: #00ff88; padding: 20px; }
                .original { border: 1px solid #00ff88; padding: 15px; margin: 20px 0; background: rgba(0,255,136,0.1); }
                h1 { color: #00ffff; text-align: center; }
                a { color: #00ff88; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>📚 Meta-Automata Documentation Archive</h1>
            <div class="original">
                <h2>Original Repository Structure (Preserved)</h2>
                <ul>
                    <li><a href="/README.md">README.md</a> - Original project overview</li>
                    <li><a href="/migration_guide.md">migration_guide.md</a> - Device migration documentation</li>
                    <li><a href="/.github/">.github/</a> - Original GitHub configuration</li>
                </ul>
            </div>
            <p><a href="/">← Back to Meta-Automata Interface</a></p>
        </body>
        </html>
        """
        
        return HTMLResponse(docs_html)
        
    async def _get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        
        status = {
            "timestamp": time.time(),
            "meta_automata_active": self.meta_automata.is_running if self.meta_automata else False,
            "learning_cycle": self.meta_automata.learning_cycle if self.meta_automata else 0,
            "vulkan_available": False,
            "ai_services_count": 0
        }
        
        # Get Vulkan status
        if hasattr(self.meta_automata, 'vulkan_renderer') and self.meta_automata.vulkan_renderer:
            vulkan_state = await self.meta_automata.vulkan_renderer.get_state()
            status["vulkan_available"] = vulkan_state.get("vulkan_available", False)
            
        # Get AI services status
        if hasattr(self.meta_automata, 'ai_orchestrator') and self.meta_automata.ai_orchestrator:
            ai_feedback = await self.meta_automata.ai_orchestrator.get_system_feedback()
            status["ai_services_count"] = ai_feedback.get("service_count", 0)
            
        return status
        
    async def _get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        
        if self.meta_automata:
            return self.meta_automata.get_metrics()
        else:
            return {
                "patterns_learned": 0,
                "adaptations_made": 0,
                "prediction_accuracy": 0.0,
                "processing_speed": 0.0
            }
            
    async def _get_patterns(self) -> Dict[str, Any]:
        """Get learning patterns"""
        
        if self.meta_automata:
            patterns = self.meta_automata.get_patterns()
            return {
                "patterns": [
                    {
                        "id": p.pattern_id,
                        "confidence": p.confidence,
                        "usage_count": p.usage_count,
                        "timestamp": p.timestamp
                    }
                    for p in patterns.values()
                ],
                "total_count": len(patterns)
            }
        else:
            return {"patterns": [], "total_count": 0}
            
    async def _get_config(self) -> Dict[str, Any]:
        """Get system configuration"""
        
        return {
            "ai": {
                "services_configured": bool(self.config_manager.get_ai_config().gemini_api_key or 
                                         self.config_manager.get_ai_config().openai_api_key)
            },
            "system": {
                "vulkan_enabled": self.config_manager.get_system_config().vulkan_enabled,
                "cuda_enabled": self.config_manager.get_system_config().cuda_enabled,
                "max_workers": self.config_manager.get_system_config().max_workers
            },
            "learning": {
                "adaptation_rate": self.config_manager.get_learning_config().adaptation_rate,
                "memory_depth": self.config_manager.get_learning_config().memory_depth
            }
        }
        
    async def _update_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update system configuration"""
        
        try:
            for section, values in config_data.items():
                for key, value in values.items():
                    self.config_manager.update_config(section, key, value)
                    
            await self.config_manager.save_config()
            
            return {"status": "success", "message": "Configuration updated"}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    async def _get_ai_services(self) -> List[Dict[str, Any]]:
        """Get AI service status"""
        
        services = []
        
        if hasattr(self.meta_automata, 'ai_orchestrator') and self.meta_automata.ai_orchestrator:
            orchestrator = self.meta_automata.ai_orchestrator
            
            for service_name in ["gemini", "openai", "github_copilot"]:
                active = service_name in orchestrator.services
                services.append({
                    "name": service_name.replace("_", " ").title(),
                    "active": active,
                    "status": "Active" if active else "Not Configured"
                })
        else:
            for service_name in ["Gemini", "OpenAI", "GitHub Copilot"]:
                services.append({
                    "name": service_name,
                    "active": False,
                    "status": "Not Available"
                })
                
        return services
        
    async def _ai_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send query to AI services"""
        
        try:
            if not hasattr(self.meta_automata, 'ai_orchestrator') or not self.meta_automata.ai_orchestrator:
                return {"error": "AI orchestrator not available"}
                
            response = await self.meta_automata.ai_orchestrator.generate_consensus_response(
                query_data.get("prompt", ""),
                query_data.get("context", {})
            )
            
            return {
                "service": response.service,
                "content": response.content,
                "confidence": response.confidence,
                "timestamp": response.timestamp
            }
            
        except Exception as e:
            return {"error": str(e)}
            
    async def _handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection"""
        
        await self.websocket_manager.connect(websocket)
        
        try:
            while True:
                # Send periodic updates
                await asyncio.sleep(1)
                
                # Send status update
                status = await self._get_system_status()
                await self.websocket_manager.send_personal_message(
                    json.dumps({"type": "status", "data": status}),
                    websocket
                )
                
                # Send metrics update
                metrics = await self._get_metrics()
                await self.websocket_manager.send_personal_message(
                    json.dumps({"type": "metrics", "data": metrics}),
                    websocket
                )
                
        except WebSocketDisconnect:
            self.websocket_manager.disconnect(websocket)
            
    async def start(self):
        """Start the web server"""
        
        system_config = self.config_manager.get_system_config()
        
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=system_config.port,
            log_level="info"
        )
        
        self.server = uvicorn.Server(config)
        self.is_running = True
        
        logger.info(f"Starting web server on port {system_config.port}")
        await self.server.serve()
        
    async def stop(self):
        """Stop the web server"""
        
        if self.server:
            self.server.should_exit = True
            
        self.is_running = False
        logger.info("Web server stopped")
