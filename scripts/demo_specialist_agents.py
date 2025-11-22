#!/usr/bin/env python3
"""
Demonstration script for MRI analysis tool and specialist agents.
This shows how the new features work without requiring a full agent setup.
"""

from medagent.infrastructure.external.simulators import tool_analyze_mri
from medagent.config.prompts import PATHOLOGY_PROMPT, RADIOLOGY_PROMPT, NEUROLOGY_PROMPT


def demo_mri_analysis():
    """Demonstrate MRI analysis for different conditions."""
    print("=" * 80)
    print("MRI Analysis Tool Demonstration")
    print("=" * 80)
    
    test_cases = [
        ("brain", "acute stroke", "Brain - Acute Stroke"),
        ("brain", "hemorrhage", "Brain - Hemorrhage"),
        ("brain", "multiple sclerosis", "Brain - Multiple Sclerosis"),
        ("spine", "disc herniation", "Spine - Disc Herniation"),
        ("brain", "", "Brain - Normal Study"),
    ]
    
    for region, context, description in test_cases:
        print(f"\n{'=' * 80}")
        print(f"Test Case: {description}")
        print(f"Region: {region} | Clinical Context: {context or 'None'}")
        print("-" * 80)
        
        result = tool_analyze_mri(region, context)
        print(result)
        print()


def demo_specialist_prompts():
    """Show specialist agent prompts."""
    print("=" * 80)
    print("Specialist Agent Prompts")
    print("=" * 80)
    
    specialists = [
        ("Pathology", PATHOLOGY_PROMPT),
        ("Radiology", RADIOLOGY_PROMPT),
        ("Neurology", NEUROLOGY_PROMPT),
    ]
    
    for name, prompt in specialists:
        print(f"\n{'=' * 80}")
        print(f"{name} Specialist Agent")
        print("-" * 80)
        # Show first 300 characters of the prompt
        preview = prompt[:300] + "..." if len(prompt) > 300 else prompt
        print(preview)
        print(f"\nTotal prompt length: {len(prompt)} characters")
        print(f"Key capabilities mentioned: ", end="")
        
        # Extract key terms
        key_terms = []
        if "Laboratory" in prompt:
            key_terms.append("Laboratory Medicine")
        if "MRI" in prompt:
            key_terms.append("MRI Analysis")
        if "neurological" in prompt.lower():
            key_terms.append("Neurological Assessment")
        if "Radiology" in prompt:
            key_terms.append("Imaging Interpretation")
        
        print(", ".join(key_terms))


if __name__ == "__main__":
    print("\n" + "🏥 " * 20)
    print("Medical Agent - Specialist Tools & MRI Analysis Demo")
    print("🏥 " * 20 + "\n")
    
    demo_mri_analysis()
    
    print("\n" + "=" * 80 + "\n")
    
    demo_specialist_prompts()
    
    print("\n" + "✅ " * 20)
    print("Demo Complete!")
    print("✅ " * 20 + "\n")
