#!/usr/bin/env python3
"""
Test script to list available Bedrock models
"""
import boto3
import json

def list_available_models():
    """List all available Bedrock foundation models"""
    try:
        bedrock = boto3.client(
            service_name="bedrock",
            region_name="eu-central-1"
        )
        
        response = bedrock.list_foundation_models()
        
        print("Available Bedrock Models:")
        print("=" * 50)
        
        for model in response['modelSummaries']:
            model_id = model.get('modelId', 'Unknown')
            model_name = model.get('modelName', 'Unknown')
            provider = model.get('providerName', 'Unknown')
            status = model.get('modelLifecycleStatus', 'Unknown')
            
            print(f"ID: {model_id}")
            print(f"Name: {model_name}")
            print(f"Provider: {provider}")
            print(f"Status: {status}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Error listing models: {str(e)}")

if __name__ == "__main__":
    list_available_models()
