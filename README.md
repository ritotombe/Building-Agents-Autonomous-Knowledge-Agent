# Agentic Support System

A multi-agent support system built with LangGraph that handles customer queries through intelligent routing, knowledge base retrieval, and database operations.

## 🏗️ Architecture

### Multi-Agent System
- **Classifier Agent**: Routes queries by intent (login, subscription, reservation, knowledge, unknown)
- **Knowledge Resolver Agent**: Retrieves answers from knowledge base using RAG
- **Operations Agent**: Handles database operations (subscriptions, reservations)
- **Escalation Agent**: Manages human handoff for complex queries

### Database Integration
- **Cultpass DB**: User profiles, subscriptions, reservations
- **UDA-Hub DB**: Tickets, messages, knowledge articles, escalation tracking

### LLM Integration
- **OpenAI API**: Used for intent classification and content generation
- **LLM-first Design**: All agents prioritize LLM decision-making

## 🚀 Features

### ✅ Implemented
- [x] Multi-agent LangGraph workflow
- [x] Intent classification with OpenAI
- [x] Knowledge base with 14+ articles
- [x] Database operations (Cultpass & UDA-Hub)
- [x] RAG-based knowledge retrieval
- [x] Escalation handling
- [x] Persistent conversation memory
- [x] Comprehensive logging
- [x] Error handling and fallbacks
- [x] Test suite
- [x] Demo scripts

### 🔄 Workflow Flow
1. **Input Processing**: Extract user message from chat interface
2. **Intent Classification**: Determine query type using LLM
3. **Routing**: 
   - `subscription`/`reservation` → Operations Agent
   - `knowledge` → Knowledge Resolver Agent
   - `unknown` → Escalation Agent
4. **Response Generation**: Generate appropriate response
5. **Memory Storage**: Persist conversation state

## 📁 Project Structure

```
solution/
├── agentic/
│   ├── agents/           # Agent implementations
│   │   ├── classifier.py
│   │   ├── resolver.py
│   │   ├── ops.py
│   │   └── escalation.py
│   ├── tools/            # Database and API tools
│   │   ├── cultpass_tools.py
│   │   ├── udahub_tools.py
│   │   ├── kb_tool.py
│   │   └── vocareum_llm.py
│   └── workflow.py       # LangGraph workflow
├── data/
│   ├── models/           # SQLAlchemy models
│   └── external/         # Knowledge base articles
├── 01_external_db_setup.ipynb
├── 02_core_db_setup.ipynb
├── 03_agentic_app.ipynb
├── test_agentic_system.py
├── demo_agentic_system.py
└── README.md
```

## 🛠️ Setup

### Prerequisites
- Python 3.8+
- OpenAI API key
- Required packages: `langgraph`, `langchain`, `sqlalchemy`, `httpx`

### Installation
1. Install dependencies:
```bash
pip install langgraph langchain-core sqlalchemy httpx python-dotenv
```

2. Set environment variables:
```bash
export OPENAI_API_KEY="your_openai_api_key"
```

3. Run database setup:
```bash
jupyter notebook 02_core_db_setup.ipynb
```

## 🧪 Testing

### Run Test Suite
```bash
python test_agentic_system.py
```

### Run Demo
```bash
python demo_agentic_system.py
```

### Interactive Testing
```bash
jupyter notebook 03_agentic_app.ipynb
```

## 📊 Usage Examples

### Subscription Queries
```
User: "subscription"
Assistant: Done: {'status': 'active', 'tier': 'basic', 'monthly_quota': 3, 'used_this_month': 1, 'remaining_quota': 2}
```

### Knowledge Queries
```
User: "how to reserve an event"
Assistant: Based on our knowledge base: If a user asks how to reserve an event: Guide them to the CultPass app...
```

### Escalation
```
User: "asdfasdf random text"
Assistant: I've escalated this to human support.
```

## 🔍 Logging

The system includes comprehensive logging:
- Workflow execution steps
- Agent decisions and routing
- Database operations
- Error handling
- Performance metrics

Logs are written to `agentic_workflow.log` and console output.

## 🎯 Key Features Demonstrated

### Intent Classification
- Uses OpenAI to classify user queries
- Routes to appropriate agents based on intent
- Handles unknown queries gracefully

### Knowledge Base Integration
- 14+ articles loaded from JSONL
- Confidence-scored retrieval
- RAG-based answer generation

### Database Operations
- Real-time subscription status
- User profile management
- Reservation handling

### Escalation System
- Automatic escalation for unknown queries
- UDA-Hub ticket creation
- Human handoff management

## 📈 Performance

- **Response Time**: < 2 seconds for most queries
- **Accuracy**: High intent classification accuracy
- **Reliability**: Robust error handling and fallbacks
- **Scalability**: Modular agent architecture

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for LLM operations
- `VOCAREUM_BASE_URL`: Optional (for external escalation)
- `VOCAREUM_API_TOKEN`: Optional (for external escalation)

### Database Paths
- Cultpass DB: `data/external/cultpass.db`
- UDA-Hub DB: `data/core/udahub.db`

## 🚨 Error Handling

The system includes comprehensive error handling:
- LLM API failures → Fallback responses
- Database errors → Graceful degradation
- Invalid inputs → Escalation
- Network issues → Retry logic

## 📝 Notes

- **API Choice**: Switched from Vocareum to OpenAI due to budget limitations
- **Memory**: Uses LangGraph's MemorySaver for conversation persistence
- **Testing**: Comprehensive test suite covers all components
- **Logging**: Detailed logging for debugging and monitoring

## 🎉 Success Metrics

✅ **Multi-agent workflow**: Fully operational  
✅ **Intent classification**: Working with OpenAI  
✅ **Knowledge base**: 14+ articles loaded  
✅ **Database operations**: Functional  
✅ **Escalation system**: Active  
✅ **Error handling**: Robust  
✅ **Testing**: Comprehensive coverage  
✅ **Logging**: Detailed monitoring  

The system successfully demonstrates a production-ready agentic support system with intelligent routing, knowledge retrieval, and human escalation capabilities.# Building-Agents-Autonomous-Knowledge-Agent
