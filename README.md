# Hisper - MCP Server Discovery Interface

🚀 **Hisper** is an intelligent interface for discovering and managing Model Context Protocol (MCP) servers across various domains. It automatically searches for MCP servers from multiple sources and provides a unified platform for task routing and execution.

## Features

### 🔍 **Intelligent Server Discovery**
- **Multi-source Discovery**: Automatically discovers MCP servers from GitHub, npm, PyPI, and other sources
- **Real-time Monitoring**: Continuous health monitoring and status tracking
- **Smart Categorization**: Automatically categorizes servers based on their capabilities
- **Manual Addition**: Support for manually adding custom MCP servers

### 🎯 **Task Management & Routing**
- **Intelligent Routing**: Routes tasks to the most appropriate MCP servers based on capabilities
- **Priority Management**: Support for task prioritization (urgent, high, normal, low)
- **Real-time Execution**: Live monitoring of task execution with WebSocket updates
- **Retry Logic**: Automatic retry mechanisms with configurable limits

### 📊 **Monitoring & Analytics**
- **Health Dashboards**: Real-time server health and performance monitoring
- **Usage Statistics**: Track server usage, success rates, and performance metrics
- **Task Analytics**: Comprehensive task execution analytics and reporting
- **WebSocket Updates**: Real-time updates for all system events

### 🌐 **Modern Web Interface**
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Real-time Updates**: Live data updates without page refreshes
- **Intuitive Navigation**: Clean, modern interface built with React and Tailwind CSS
- **Dark/Light Mode**: Support for different themes (coming soon)

## Architecture

```
hisper/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── requirements.txt
│   └── main.py
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── utils/          # Utility functions
│   ├── package.json
│   └── public/
├── docker-compose.yml      # Docker orchestration
└── README.md
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hisper
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:12001
   - Backend API: http://localhost:12000
   - API Documentation: http://localhost:12000/docs

### Local Development

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub API token for server discovery | None |
| `DATABASE_URL` | Database connection string | `sqlite:///./hisper.db` |
| `DISCOVERY_INTERVAL_MINUTES` | How often to run discovery | `60` |
| `MAX_CONCURRENT_DISCOVERIES` | Max concurrent discovery tasks | `10` |
| `SECRET_KEY` | JWT secret key | Change in production |
| `DEBUG` | Enable debug mode | `false` |

### Discovery Sources

Hisper supports multiple discovery sources:

- **GitHub**: Searches for repositories with MCP server implementations
- **npm**: Discovers MCP servers published as npm packages
- **PyPI**: Finds Python-based MCP servers on PyPI
- **Manual**: Allows manual addition of custom servers

## API Documentation

The backend provides a comprehensive REST API with automatic OpenAPI documentation:

- **Interactive Docs**: http://localhost:12000/docs
- **OpenAPI Schema**: http://localhost:12000/openapi.json

### Key Endpoints

- `GET /api/v1/servers` - List all discovered servers
- `POST /api/v1/servers` - Add a new server
- `GET /api/v1/tasks` - List all tasks
- `POST /api/v1/tasks` - Create a new task
- `POST /api/v1/discovery/start` - Start server discovery
- `GET /api/v1/discovery/status` - Get discovery status

## WebSocket Events

Real-time updates are provided via WebSocket connection at `/ws`:

- `server_discovered` - New server discovered
- `server_health_update` - Server health status changed
- `task_update` - Task status updated
- `task_completed` - Task execution completed
- `discovery_status` - Discovery process status

## Development

### Project Structure

- **Backend**: FastAPI with SQLAlchemy, async support, and comprehensive API
- **Frontend**: React with TypeScript, Tailwind CSS, and React Query
- **Database**: SQLite (development) / PostgreSQL (production)
- **Caching**: Redis for task queues and caching
- **WebSockets**: Real-time updates and notifications

### Adding New Discovery Sources

1. Create a new discovery method in `DiscoveryService`
2. Add API endpoint in `discovery.py`
3. Update frontend to support the new source
4. Add configuration options as needed

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Deployment

### Production Deployment

1. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Configure production values
   ```

2. **Use production Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Set up reverse proxy** (nginx, Traefik, etc.)

4. **Configure SSL certificates**

### Scaling

- Use PostgreSQL for the database in production
- Set up Redis cluster for high availability
- Use container orchestration (Kubernetes, Docker Swarm)
- Implement load balancing for multiple backend instances

## Monitoring

Hisper includes built-in monitoring capabilities:

- **Health Checks**: Automatic health monitoring for all servers
- **Metrics**: Performance and usage metrics
- **Logging**: Comprehensive logging with configurable levels
- **Alerts**: Configurable alerts for system events

## Security

- **API Authentication**: JWT-based authentication (optional)
- **CORS Configuration**: Configurable CORS policies
- **Input Validation**: Comprehensive input validation and sanitization
- **Rate Limiting**: Built-in rate limiting for API endpoints

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Documentation**: Check the `/docs` endpoint for API documentation
- **Issues**: Report bugs and feature requests via GitHub issues
- **Discussions**: Join community discussions for questions and ideas

## Roadmap

- [ ] MCP Protocol Implementation
- [ ] Advanced Task Scheduling
- [ ] Plugin System
- [ ] Multi-tenant Support
- [ ] Advanced Analytics
- [ ] Mobile App
- [ ] AI-powered Server Recommendations

---

**Hisper** - Making MCP server discovery and management effortless! 🚀
