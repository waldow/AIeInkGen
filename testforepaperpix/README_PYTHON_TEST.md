# Python Test Script for SendAIData

This Python script (`test_send_ai_data.py`) replicates the functionality of the C# `ImagesController.SendAIData` method, allowing you to test AI image generation requests independently.

## Features

- **Full AIGenerationModel Implementation**: Mirrors the C# model with all fields
- Sends AI generation requests to Azure Service Bus queue ("genai")
- Supports all content types: date, text, image, and **image_text** (NEW)
- **OpenAI Integration**: Generate descriptive image text using GPT models
- **Weather API Support**: Create weather-based image descriptions
- Calculates token costs based on MagicMode and ContentType
- Token validation and consumption simulation
- Rotation support (swaps width/height when enabled)
- Multiple generation styles (artistic, minimalist, tech, weather)
- Provides comprehensive logging
- Includes comprehensive test scenarios

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and update with your values:

```bash
cp .env.example .env
```

Edit `.env` with your Azure Service Bus connection string:
```
AZURE_SERVICE_BUS_CONNECTION_STRING=Endpoint=sb://...
TEST_ACCOUNT_ID=your-account-id
```

## Usage

### Run All Tests
```bash
python test_send_ai_data.py
```

### Run Specific Test Types

Test date generation:
```bash
python test_send_ai_data.py date
```

Test text generation with custom text:
```bash
python test_send_ai_data.py text "Your custom text here"
```

Test image generation with custom URL:
```bash
python test_send_ai_data.py image "https://example.com/your-image.jpg"
```

### Model-Based Tests (C# Style)

Test with AIGenerationModel directly:
```bash
python test_send_ai_data.py model
```

Test rotation feature:
```bash
python test_send_ai_data.py rotate
```

Test insufficient tokens scenario:
```bash
python test_send_ai_data.py tokens
```

### Image Text Generation (NEW)

Generate AI-powered descriptive text for images:
```bash
# Basic image_text generation
python test_send_ai_data.py image_text

# With custom input and style
python test_send_ai_data.py image_text "A serene mountain landscape" "minimalist"
python test_send_ai_data.py image_text "Futuristic city skyline" "tech"

# Available styles: artistic, minimalist, tech, weather_basic, weather_detailed
```

### Weather-based Image Text

Generate weather visualization descriptions:
```bash
# Default location (London)
python test_send_ai_data.py weather

# Specific location
python test_send_ai_data.py weather "New York"
python test_send_ai_data.py weather "Tokyo"
```

### Test Multiple Styles

Test all available generation styles:
```bash
python test_send_ai_data.py styles
```

### Custom Model Test

Create a fully custom test with all parameters:
```bash
python test_send_ai_data.py custom "job-id" "content-type" "theme" "magic-mode" "content"

# Examples:
python test_send_ai_data.py custom "job-001" "text" "Cyberpunk theme" 2 "Hello World"
python test_send_ai_data.py custom "job-002" "image" "" 4 "https://example.com/img.jpg"
python test_send_ai_data.py custom "job-003" "date" "Elegant calendar" 1
python test_send_ai_data.py custom "job-004" "image_text" "Modern art" 2 "Abstract composition"
```

## Message Structure

The script sends messages to the Service Bus with the following structure:

```json
{
  "accountId": "test-account-123",
  "image_id": "uuid-here",
  "width": 400,
  "height": 300,
  "content_type": "date|text|image",
  "theme": "Theme description",
  "jobName": "test-job-name",
  "magic_mode": 1,
  "user_date": "15 January 2024",  // for date type
  "user_text": "Sample text",       // for text type
  "image_url": "https://..."        // for image type
}
```

## Token Cost Calculation

Token costs are calculated based on:
- **MagicMode 1 (Low)**: Base cost (1 token)
- **MagicMode 2 (Medium)**: 4 tokens for images, 2 for text/date
- **MagicMode 4 (High)**: 4 tokens for all content types

## AIGenerationModel Fields

The Python AIGenerationModel class includes all fields from the C# model:

```python
model = AIGenerationModel()
model.id = "job-001"                    # Job ID
model.image_id = "uuid"                 # Auto-generated GUID
model.width = 800                       # Image width
model.height = 480                      # Image height
model.rotate = False                    # Swap width/height if True
model.is_date = False                   # Is date content type
model.content_type = "text"             # "text", "date", "image", or "image_text"
model.date = datetime.now()             # Date for date content
model.text = "Sample text"              # Text for text content
model.image_url = "https://..."         # URL for image content
model.image_text = "Generated text"     # AI-generated descriptive text (NEW)
model.system_prompt = "Style prompt"    # System prompt for AI generation (NEW)
model.theme = "Theme description"       # AI generation theme
model.magic_mode = 1                    # 1=Low, 2=Medium, 4=High
model.available_tokens = 100            # User's available tokens
model.token_cost_per_generation = 1     # Calculated token cost
model.has_sufficient_tokens = True      # Token validation result
```

## Image Text Content Type

The `image_text` content type is a powerful new feature that:
1. Accepts input text or data (weather, custom text, etc.)
2. Uses OpenAI to generate descriptive image prompts
3. Sends the generated text to the Service Bus as regular text content
4. Supports multiple generation styles for different aesthetics

### Generation Styles

- **artistic**: Vivid imagery and creative composition
- **minimalist**: Clean, simple, elegant descriptions
- **tech**: Futuristic, digital aesthetics
- **weather_basic**: Weather display with temperature focus
- **weather_detailed**: Enhanced weather visualization

## Test Scenarios

The script includes the following test scenarios:
1. Date Generation (Portrait orientation)
2. Date Generation (Landscape orientation)
3. Text Generation (Low Magic Mode)
4. Text Generation (Medium Magic Mode)
5. Text Generation (High Magic Mode)
6. Image Generation (High Magic Mode)
7. Model-based Text Generation (C# style)
8. Model-based with Rotation
9. Insufficient Tokens Test
10. **Image Text Generation** (NEW)
11. **Weather-based Image Text** (NEW)
12. **Multiple Styles Test** (NEW)

## Logging

The script provides detailed logging including:
- Message payloads being sent
- Token costs for each generation
- Success/failure status
- Test summary with pass/fail counts

## Troubleshooting

If you encounter connection issues:
1. Verify your Service Bus connection string is correct
2. Ensure the "genai" queue exists in your Service Bus namespace
3. Check that your connection string has Send permissions
4. Verify network connectivity to Azure

## Integration with C# Application

This Python script sends the exact same message format as the C# application's `SendAIData` method. The messages are processed by the same backend service that handles the web application's requests.