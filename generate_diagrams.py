#!/usr/bin/env python3
"""
Simple script to generate LangGraph workflow diagrams.
Run this to create visual diagrams of the agentic system workflow.
"""

import os
import sys
from pathlib import Path

# Add solution to path
sys.path.insert(0, str(Path(__file__).parent))

def generate_diagrams():
    """Generate workflow diagrams."""
    
    print("🎯 LangGraph Workflow Diagram Generator")
    print("=" * 50)
    
    try:
        # Import the orchestrator
        from agentic.workflow import orchestrator
        from langchain_core.runnables.graph import MermaidDrawMethod
        
        print("📊 Building workflow graph...")
        graph = orchestrator.get_graph()
        
        # Generate Mermaid text
        print("📝 Generating Mermaid diagram text...")
        mermaid_text = graph.draw_mermaid()
        
        # Save Mermaid text
        with open("workflow_diagram.mmd", "w") as f:
            f.write(mermaid_text)
        print("✅ Mermaid text saved to: workflow_diagram.mmd")
        
        # Try to generate PNG
        print("🎨 Attempting to generate PNG diagram...")
        try:
            diagram_bytes = graph.draw_mermaid_png(
                draw_method=MermaidDrawMethod.API
            )
            
            with open("workflow_diagram.png", "wb") as f:
                f.write(diagram_bytes)
            print("✅ PNG diagram saved to: workflow_diagram.png")
            
        except Exception as png_error:
            print(f"⚠️  PNG generation failed: {png_error}")
            print("📝 But Mermaid text was generated successfully!")
        
        # Display the Mermaid text
        print("\n📊 Generated Mermaid Diagram:")
        print("=" * 50)
        print("```mermaid")
        print(mermaid_text)
        print("```")
        
        print("\n💡 Usage:")
        print("   - Copy the Mermaid code above to GitHub/GitLab")
        print("   - Use Mermaid Live Editor: https://mermaid.live/")
        print("   - Install Mermaid extension in VS Code")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure you're in the solution directory")
        print("2. Check that agentic.workflow imports correctly")
        print("3. Verify LangGraph installation")
        return False

if __name__ == "__main__":
    success = generate_diagrams()
    if success:
        print("\n🎉 Diagram generation complete!")
    else:
        print("\n❌ Diagram generation failed")
