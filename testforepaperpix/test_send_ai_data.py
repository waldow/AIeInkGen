#!/usr/bin/env python3
"""
Test script for SendAIData functionality
Replicates the C# ImagesController.SendAIData method behavior
Sends AI generation requests to Azure Service Bus
"""

import json
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Optional, Any, List
import logging
import re
from xml.parsers.expat import model

# Azure Service Bus import
try:
    from azure.servicebus import ServiceBusClient, ServiceBusMessage
except ImportError:
    print("Please install azure-servicebus: pip install azure-servicebus")
    sys.exit(1)

# OpenAI import (optional for image_text generation)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI not installed. Image text generation will be limited.")

# Requests for weather API (optional)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not installed. Weather features will be limited.")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using system environment variables only.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIGenerationModel:
    """Python representation of C# AIGenerationModel"""
    
    def __init__(self):
        self.id = None  # Job ID
        self.image_id = str(uuid.uuid4())
        self.width = 400
        self.height = 300
        self.rotate = False
        self.is_date = False
        self.content_type = "text"  # "text", "date", "image", or "image_text"
        self.date = datetime.now()
        self.text = ""
        self.image_url = ""
        self.theme = ""
        self.magic_mode = 1  # 1=Low, 2=Medium, 4=High
        self.available_tokens = 100  # For display/testing purposes
        self.token_cost_per_generation = 1
        self.has_sufficient_tokens = True
        self.image_text = ""  # Generated descriptive text for image_text content type
        self.system_prompt = ""  # System prompt for AI text generation
    
    def to_dict(self):
        """Convert to dictionary for display"""
        return {
            "id": self.id,
            "image_id": self.image_id,
            "width": self.width,
            "height": self.height,
            "rotate": self.rotate,
            "is_date": self.is_date,
            "content_type": self.content_type,
            "date": self.date.isoformat() if isinstance(self.date, datetime) else self.date,
            "text": self.text,
            "image_url": self.image_url,
            "theme": self.theme,
            "magic_mode": self.magic_mode,
            "available_tokens": self.available_tokens,
            "token_cost_per_generation": self.token_cost_per_generation,
            "has_sufficient_tokens": self.has_sufficient_tokens
        }


class AIGenerationTester:
    """Test class for AI generation via Service Bus"""
    
    # System prompts for different generation styles
    SYSTEM_PROMPTS = {
        "weather_basic": """You are good at image text generation for a given weather and describe the image. 
        Make it display the temperature in big text. Make sure the background matches the time of day. 
        The color palette is limited to black, white, red and yellow. The scene is cheerful and simplistic, 
        emphasizing the contrast between the colors. Image should fit full resolution. No drawing utensils.""",
        
        "weather_detailed": """You are good at image text generation for weather data. Create a visually appealing 
        description with temperature prominently displayed. Include weather conditions in 3 words or less. 
        Color palette: black, white, red, yellow. Make it pop with high contrast. Match time of day in background.""",

        "weather_good": """You are good in image text generation for a given weather and describe the image. 
        Make a closup and some pop. Make it display the temperature in big  text. Make sure the background match the time of day, day or night.  
        The color palette is limited to black, white , red and yellow. The scene is cheerful and simplistic, emphasizing the contrast between the colors. 
        Image on fit full resolution.No explanation just the Description.""",
        
        "artistic": """Create an artistic and visually striking image description. Use vivid imagery and creative 
        composition. Limited color palette: black, white, red. Emphasize contrast and visual impact. 
        Make the main subject prominent and eye-catching.""",
        
        "minimalist": """Generate a clean, minimalist image description. Focus on simplicity and elegance. 
        Use negative space effectively. Limited colors: black and white with red accents. 
        Emphasize typography and clean lines.""",
        
        "tech": """Create a futuristic, tech-inspired image description. Use geometric shapes and digital aesthetics. 
        Include data visualization elements. Color palette: black, white, with neon accents. 
        Make it look modern and cutting-edge."""
    }
    
    def __init__(self, connection_string: Optional[str] = None):
        """Initialize the tester with Service Bus connection"""
        self.connection_string = connection_string or os.getenv('AZURE_SERVICE_BUS_CONNECTION_STRING')
        if not self.connection_string:
            raise ValueError("Service Bus connection string not provided. Set AZURE_SERVICE_BUS_CONNECTION_STRING environment variable.")
        
        self.queue_name = "genai"
        self.account_id = os.getenv('TEST_ACCOUNT_ID', 'test-account-123')
        
        # Initialize OpenAI client if available
        self.openai_client = None
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = OpenAI()  #api_key=api_key)
                logger.info("OpenAI client initialized successfully")
            else:
                logger.warning("OPENAI_API_KEY not set. Image text generation will be limited.")
        
        # Weather API configuration
        self.weather_api_key = os.getenv('WEATHER_API_KEY')
        self.weather_api_base = "http://api.weatherapi.com/v1"
        
    def format_weather_data(self, data: Dict[str, Any]) -> str:
        """Format weather data into readable text (from imagegenweather.py)"""
        if not data:
            return "Weather data unavailable"
        
        location = data.get('location', {})
        current = data.get('current', {})
        condition = current.get('condition', {})
        
        readable_text = (
            f"Weather Information for {location.get('name', 'Unknown')}\n"
            f"Local Time: {location.get('localtime', 'N/A')}\n\n"
            f"Current Conditions:\n"
            f"  - Temperature: {current.get('temp_c', 'N/A')}°C\n"
            f"  - Condition: {condition.get('text', 'N/A')}\n"
            f"  - Cloud Cover: {current.get('cloud', 'N/A')}%\n"
        )
        
        return readable_text
    
    def fetch_weather_data(self, location: str = "London") -> Optional[Dict[str, Any]]:
        """Fetch weather data from API"""
        if not REQUESTS_AVAILABLE:
            logger.warning("requests library not available. Cannot fetch weather data.")
            return None
        
        if not self.weather_api_key:
            logger.warning("Weather API key not set. Using sample data.")
            # Return sample weather data for testing
            return {
                "location": {"name": location, "localtime": datetime.now().strftime("%Y-%m-%d %H:%M")},
                "current": {
                    "temp_c": 22,
                    "condition": {"text": "Partly cloudy"},
                    "cloud": 40
                }
            }
        
        try:
            url = f"{self.weather_api_base}/current.json"
            params = {"key": self.weather_api_key, "q": location}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch weather data: {e}")
            return None
    
    def generate_image_text(self, 
                          input_text: str, 
                          system_prompt: Optional[str] = None,
                          model: str = "gpt-5-mini") -> str:
        """
        Generate descriptive image text using OpenAI
        Enhanced version of imagegenweather.py functionality
        """
        if not self.openai_client:
            logger.warning("OpenAI client not available. Returning input text.")
            return input_text
        
        if not system_prompt:
            system_prompt = self.SYSTEM_PROMPTS.get("artistic", "Generate a creative image description.")
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text}
            ]
            # max_tokens=500,temperature=0.8
            completion = self.openai_client.chat.completions.create(
                model=model,
                messages=messages
               
                
            )
            
            # Clean up the generated text
            image_text = completion.choices[0].message.content
            image_text = image_text.replace('**"', '"').replace("**", '"')
            
            logger.info(f"Generated image text: {image_text[:100]}...")
            return image_text
            
        except Exception as e:
            logger.error(f"Failed to generate image text: {e}")
            return input_text
    
    def calculate_token_cost(self, magic_mode: int, content_type: str, base_token_cost: int = 1) -> int:
        """
        Calculate token cost based on MagicMode and ContentType
        Replicates C# CalculateTokenCost method
        
        Magic Mode levels: 1=Low, 2=Medium, 4=High
        """
        # image_text has same cost as image
        if content_type in ["image", "image_text"]:
            if magic_mode == 2:  # Medium
                return 4
            elif magic_mode == 4:  # High
                return 4
            else:  # Low
                return base_token_cost
        else:  # text, date
            if magic_mode == 2:  # Medium
                return 2
            elif magic_mode == 4:  # High
                return 4
            else:  # Low
                return base_token_cost
    
    def create_genai_message_from_model(self, model: AIGenerationModel) -> Dict[str, Any]:
        """
        Create the GenAIdateThemeSB message payload from AIGenerationModel
        Matches the C# BuilderRequestGenAISB method
        """
        # Apply rotation if needed (swap width and height)
        width = model.height if model.rotate else model.width
        height = model.width if model.rotate else model.height
        
        message = {
            "accountId": self.account_id,
            "image_id": model.image_id,
            "mode": "holding",
            "width": width,
            "height": height,
            "content_type": model.content_type or ("date" if model.is_date else "text"),
            "user_image_text": model.theme,
            "jobName": model.id or f"test-job-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "magic_mode": model.magic_mode
        }
        
        # Set content based on content type (matches C# logic)
        if message["content_type"] == "date":
            # Format date as "d MMMM yyyy" (e.g., "15 January 2024")
            message["user_date"] = model.date.strftime("%-d %B %Y") if isinstance(model.date, datetime) else model.date
            message["user_text"] = ""
            message["image_url"] = ""
        elif message["content_type"] == "image":
            message["image_url"] = model.image_url or ""
            message["user_date"] = ""
            message["user_text"] = ""
        elif message["content_type"] == "image_text":
            # For image_text, we send the generated descriptive text
            message["user_text"] = model.image_text or model.text or ""
            message["user_date"] = ""
            message["image_url"] = ""
            # Override content_type to "text" for Service Bus (backend treats it as text)
            message["content_type"] = "text"
        else:  # text or default
            message["user_text"] = model.text or ""
            message["user_date"] = ""
            message["image_url"] = ""
        
        return message
    
    def create_genai_message(self, 
                           content_type: str,
                           width: int = 400,
                           height: int = 300,
                           theme: str = "Modern minimalist design",
                           magic_mode: int = 1,
                           job_name: str = None,
                           user_date: str = None,
                           user_text: str = None,
                           image_url: str = None) -> Dict[str, Any]:
        """
        Create the GenAIdateThemeSB message payload (legacy method for backward compatibility)
        """
        # Create a model and use the new method
        model = AIGenerationModel()
        model.id = job_name
        model.width = width
        model.height = height
        model.content_type = content_type
        model.theme = theme
        model.magic_mode = magic_mode
        model.text = user_text or ""
        model.image_url = image_url or ""
        
        if content_type == "date":
            if user_date:
                # Parse the date string if provided
                model.date = user_date
            model.is_date = True
        
        return self.create_genai_message_from_model(model)
    
    def send_to_service_bus(self, message_payload: Dict[str, Any]) -> bool:
        """
        Send message to Azure Service Bus
        Replicates C# BuilderRequestGenAISB method
        """
        try:
            # Create Service Bus client
            with ServiceBusClient.from_connection_string(self.connection_string) as client:
                # Create sender for the queue
                with client.get_queue_sender(queue_name=self.queue_name) as sender:
                    # Serialize message to JSON
                    json_payload = json.dumps(message_payload, ensure_ascii=False)
                    
                    # Create Service Bus message
                    message = ServiceBusMessage(
                        body=json_payload,
                        content_type="application/json"
                    )
                    
                    # Send the message
                    sender.send_messages(message)
                    logger.info(f"Message sent successfully. Image ID: {message_payload['image_id']}")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return False
    
    def test_date_generation(self, rotate: bool = False):
        """Test date-based AI generation"""
        logger.info("Testing DATE content type generation...")
        
        width, height = (300, 400) if rotate else (400, 300)
        
        message = self.create_genai_message(
            content_type="date",
            width=width,
            height=height,
            theme="Elegant calendar design with modern typography",
            magic_mode=1,
            user_date=datetime.now().strftime("%-d %B %Y")
        )
        
        logger.info(f"Message payload: {json.dumps(message, indent=2)}")
        
        # Calculate token cost
        token_cost = self.calculate_token_cost(message['magic_mode'], message['content_type'])
        logger.info(f"Token cost for this generation: {token_cost}")
        
        return self.send_to_service_bus(message)
    
    def test_text_generation(self, text: str = "Hello AI World!", magic_mode: int = 2):
        """Test text-based AI generation"""
        logger.info("Testing TEXT content type generation...")
        
        message = self.create_genai_message(
            content_type="text",
            width=800,
            height=480,
            theme="Vibrant tech-inspired background with floating text",
            magic_mode=magic_mode,
            user_text=text
        )
        
        logger.info(f"Message payload: {json.dumps(message, indent=2)}")
        
        # Calculate token cost
        token_cost = self.calculate_token_cost(message['magic_mode'], message['content_type'])
        logger.info(f"Token cost for this generation: {token_cost}")
        
        return self.send_to_service_bus(message)
    
    def test_image_generation(self, image_url: str = None, magic_mode: int = 4):
        """Test image-based AI generation"""
        logger.info("Testing IMAGE content type generation...")
        
        message = self.create_genai_message(
            content_type="image",
            width=1024,
            height=768,
            theme="",  # Theme is optional for image content type
            magic_mode=magic_mode,
            image_url=image_url or "https://example.com/sample-image.jpg"
        )
        
        logger.info(f"Message payload: {json.dumps(message, indent=2)}")
        
        # Calculate token cost
        token_cost = self.calculate_token_cost(message['magic_mode'], message['content_type'])
        logger.info(f"Token cost for this generation: {token_cost}")
        
        return self.send_to_service_bus(message)
    
    def send_ai_data(self, model: AIGenerationModel) -> bool:
        """
        Main method that replicates C# SendAIData functionality
        This includes token validation and consumption logic
        """
        logger.info("=" * 60)
        logger.info("SendAIData - Replicating C# Controller Method")
        logger.info("=" * 60)
        
        # Display the model data
        logger.info("AIGenerationModel Configuration:")
        for key, value in model.to_dict().items():
            logger.info(f"  {key}: {value}")
        
        # Calculate token cost
        model.token_cost_per_generation = self.calculate_token_cost(
            model.magic_mode, 
            model.content_type, 
            1  # base token cost
        )
        
        # Check if user has sufficient tokens
        model.has_sufficient_tokens = model.available_tokens >= model.token_cost_per_generation
        
        if not model.has_sufficient_tokens:
            logger.error(f"Insufficient tokens! Required: {model.token_cost_per_generation}, Available: {model.available_tokens}")
            return False
        
        logger.info(f"Token check passed. Cost: {model.token_cost_per_generation}, Available: {model.available_tokens}")
        
        # Simulate token consumption
        logger.info(f"Consuming {model.token_cost_per_generation} tokens...")
        model.available_tokens -= model.token_cost_per_generation
        logger.info(f"Tokens remaining after consumption: {model.available_tokens}")
        
        # Generate new image ID if not set
        if not model.image_id:
            model.image_id = str(uuid.uuid4())
        
        # Create and send message
        message = self.create_genai_message_from_model(model)
        
        logger.info("Sending to Service Bus...")
        logger.info(f"Message payload: {json.dumps(message, indent=2)}")
        
        success = self.send_to_service_bus(message)
        
        if success:
            logger.info(f"✓ AI Image generation request sent successfully!")
            logger.info(f"  Image ID: {model.image_id}")
            logger.info(f"  Tokens used: {model.token_cost_per_generation}")
        else:
            logger.error("✗ Failed to send AI generation request")
        
        return success
    
    def test_with_model(self):
        """Test using AIGenerationModel directly (matches C# usage)"""
        logger.info("\n" + "=" * 60)
        logger.info("Testing with AIGenerationModel (C# Style)")
        logger.info("=" * 60)
        
        # Create a model similar to C# code
        model = AIGenerationModel()
        
        # Set up like a job from C#
        model.id = "test-job-001"
        model.width = 800
        model.height = 480
        model.date = datetime.now()
        model.theme = "Futuristic cyberpunk aesthetic with neon colors"
        model.rotate = False
        model.is_date = False
        model.content_type = "text"
        model.text = "Welcome to the Future"
        model.image_url = ""
        model.magic_mode = 2  # Medium
        model.available_tokens = 50
        
        # Send using the model
        return self.send_ai_data(model)
    
    def test_rotated_image_with_model(self):
        """Test with rotation enabled (swaps width/height)"""
        logger.info("\n" + "=" * 60)
        logger.info("Testing Rotated Image Generation")
        logger.info("=" * 60)
        
        model = AIGenerationModel()
        model.id = "test-job-002"
        model.width = 400  # Will become height
        model.height = 300  # Will become width
        model.rotate = True  # Enable rotation
        model.content_type = "date"
        model.is_date = True
        model.date = datetime.now()
        model.theme = "Elegant minimalist calendar design"
        model.magic_mode = 1
        model.available_tokens = 10
        
        logger.info(f"Original dimensions: {model.width}x{model.height}")
        logger.info(f"Rotation enabled: {model.rotate}")
        logger.info("After rotation, dimensions will be swapped")
        
        return self.send_ai_data(model)
    
    def test_insufficient_tokens(self):
        """Test behavior when user doesn't have enough tokens"""
        logger.info("\n" + "=" * 60)
        logger.info("Testing Insufficient Tokens Scenario")
        logger.info("=" * 60)
        
        model = AIGenerationModel()
        model.id = "test-job-003"
        model.width = 1024
        model.height = 768
        model.content_type = "image"
        model.image_url = "https://example.com/test.jpg"
        model.magic_mode = 4  # High - costs 4 tokens
        model.available_tokens = 2  # Not enough!
        
        return self.send_ai_data(model)
    
    def test_image_text_generation(self, input_text: str = None, style: str = "artistic"):
        """Test image_text content type with AI-generated descriptive text"""
        logger.info("\n" + "=" * 60)
        logger.info("Testing IMAGE_TEXT Generation with OpenAI")
        logger.info("=" * 60)
        
        model = AIGenerationModel()
        model.id = "test-job-image-text-001"
        model.width = 800
        model.height = 480
        model.content_type = "image_text"
        model.magic_mode = 2
        model.available_tokens = 10
        
        # Input text for generation
        if not input_text:
            input_text = "Create a stunning sunset scene with mountains and a lake, peaceful and serene"
        
        # Get system prompt for the style
        system_prompt = self.SYSTEM_PROMPTS.get(style, self.SYSTEM_PROMPTS["artistic"])
        
        # Generate descriptive image text using OpenAI
        logger.info(f"Generating image text with style: {style}")
        logger.info(f"Input: {input_text}")
        
        model.image_text = self.generate_image_text(input_text, system_prompt)
        model.theme = f"Generated using {style} style"
        
        logger.info(f"Generated text: {model.image_text[:200]}...")
        
        return self.send_ai_data(model)
    
    def test_weather_image_text(self, location: str = "London"):
        """Test weather-based image_text generation"""
        logger.info("\n" + "=" * 60)
        logger.info("Testing Weather-based IMAGE_TEXT Generation")
        logger.info("=" * 60)
        
        # Fetch weather data
        weather_data = self.fetch_weather_data(location)
        if not weather_data:
            logger.error("Failed to fetch weather data")
            return False
        
        # Format weather data
        weather_text = self.format_weather_data(weather_data)
        logger.info(f"Weather data:\n{weather_text}")
        
        model = AIGenerationModel()
        model.id = "slot1"
        model.width = 800
        model.height = 480
        model.content_type = "image_text"
        model.magic_mode = 4 #highlow
        model.available_tokens = 10
        
        # Generate weather image description
        system_prompt = self.SYSTEM_PROMPTS["weather_good"]
        model.text = ""
        model.theme = self.generate_image_text(weather_text, system_prompt)
      #  model.theme = f"Weather visualization for {location}"
        print("=========================")
        print(model.theme)
        print("=========================")
        logger.info(f"Generated weather image text: {model.theme[:200]}...")
        
        return self.send_ai_data(model)
    
    def test_multiple_styles_image_text(self):
        """Test image_text generation with multiple styles"""
        logger.info("\n" + "=" * 60)
        logger.info("Testing Multiple Styles for IMAGE_TEXT")
        logger.info("=" * 60)
        
        styles_to_test = ["minimalist", "tech", "artistic"]
        input_text = "Digital transformation and innovation"
        
        results = []
        for style in styles_to_test:
            logger.info(f"\nTesting style: {style}")
            success = self.test_image_text_generation(input_text, style)
            results.append((style, success))
        
        # Summary
        logger.info("\nStyle Test Summary:")
        for style, success in results:
            status = "✓" if success else "✗"
            logger.info(f"{status} {style}")
        
        return all(success for _, success in results)
    
    def run_all_tests(self):
        """Run all test scenarios"""
        logger.info("=" * 60)
        logger.info("Starting AI Generation Tests")
        logger.info("=" * 60)
        
        tests = [
            # Legacy style tests (backward compatibility)
            ("Date Generation (Portrait)", lambda: self.test_date_generation(rotate=True)),
            ("Date Generation (Landscape)", lambda: self.test_date_generation(rotate=False)),
            ("Text Generation (Low Magic)", lambda: self.test_text_generation(magic_mode=1)),
            ("Text Generation (Medium Magic)", lambda: self.test_text_generation(magic_mode=2)),
            ("Text Generation (High Magic)", lambda: self.test_text_generation(magic_mode=4)),
            ("Image Generation (High Magic)", lambda: self.test_image_generation(magic_mode=4)),
            
            # Model-based tests (C# style)
            ("Model-based Text Generation", lambda: self.test_with_model()),
            ("Model-based with Rotation", lambda: self.test_rotated_image_with_model()),
            ("Insufficient Tokens Test", lambda: self.test_insufficient_tokens()),
            
            # Image text generation tests (new)
            ("Image Text Generation", lambda: self.test_image_text_generation()),
            ("Weather Image Text", lambda: self.test_weather_image_text()),
            ("Multiple Styles Test", lambda: self.test_multiple_styles_image_text()),
        ]
        
        results = []
        for test_name, test_func in tests:
            logger.info(f"\nRunning: {test_name}")
            logger.info("-" * 40)
            success = test_func()
            results.append((test_name, success))
            logger.info(f"Result: {'✓ SUCCESS' if success else '✗ FAILED'}")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("Test Summary")
        logger.info("=" * 60)
        for test_name, success in results:
            status = "✓ PASSED" if success else "✗ FAILED"
            logger.info(f"{status}: {test_name}")
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        logger.info(f"\nTotal: {passed}/{total} tests passed")


def main():
    """Main entry point"""
    # Check for connection string
    connection_string = os.getenv('AZURE_SERVICE_BUS_CONNECTION_STRING')
    
    if not connection_string:
        logger.error("AZURE_SERVICE_BUS_CONNECTION_STRING environment variable not set!")
        logger.info("\nTo use this test script:")
        logger.info("1. Set the AZURE_SERVICE_BUS_CONNECTION_STRING environment variable")
        logger.info("2. Optionally set TEST_ACCOUNT_ID (defaults to 'test-account-123')")
        logger.info("\nExample:")
        logger.info("export AZURE_SERVICE_BUS_CONNECTION_STRING='Endpoint=sb://...'")
        logger.info("export TEST_ACCOUNT_ID='your-account-id'")
        return 1
    
    try:
        tester = AIGenerationTester(connection_string)
        
        # Check command line arguments for specific test
        if len(sys.argv) > 1:
            test_type = sys.argv[1].lower()
            
            if test_type == "date":
                tester.test_date_generation()
            elif test_type == "text":
                text = sys.argv[2] if len(sys.argv) > 2 else "Test message"
                tester.test_text_generation(text)
            elif test_type == "image":
                url = sys.argv[2] if len(sys.argv) > 2 else None
                tester.test_image_generation(url)
            elif test_type == "model":
                # Test with AIGenerationModel directly
                tester.test_with_model()
            elif test_type == "rotate":
                # Test rotation feature
                tester.test_rotated_image_with_model()
            elif test_type == "tokens":
                # Test insufficient tokens scenario
                tester.test_insufficient_tokens()
            elif test_type == "image_text":
                # Test image_text generation
                input_text = sys.argv[2] if len(sys.argv) > 2 else None
                style = sys.argv[3] if len(sys.argv) > 3 else "artistic"
                tester.test_image_text_generation(input_text, style)
            elif test_type == "weather":
                # Test weather-based image_text
                location = sys.argv[2] if len(sys.argv) > 2 else "London"
                tester.test_weather_image_text(location)
            elif test_type == "styles":
                # Test multiple styles
                tester.test_multiple_styles_image_text()
            elif test_type == "custom":
                # Custom model test - allows full configuration
                model = AIGenerationModel()
                
                # Parse additional arguments for custom configuration
                if len(sys.argv) > 2:
                    model.id = sys.argv[2]
                if len(sys.argv) > 3:
                    model.content_type = sys.argv[3]
                if len(sys.argv) > 4:
                    model.theme = sys.argv[4]
                if len(sys.argv) > 5:
                    model.magic_mode = int(sys.argv[5])
                if len(sys.argv) > 6:
                    if model.content_type == "text":
                        model.text = sys.argv[6]
                    elif model.content_type == "image":
                        model.image_url = sys.argv[6]
                
                logger.info("Running custom model test with provided parameters")
                tester.send_ai_data(model)
            else:
                logger.info("Unknown test type. Running all tests...")
                tester.run_all_tests()
        else:
            # Run all tests by default
            tester.run_all_tests()
            
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())