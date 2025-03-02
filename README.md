# CrewAI Shopping Agent

A powerful shopping assistant built with CrewAI that helps users find products, manage their shopping cart, and complete purchases with a natural conversational interface.

## Overview

This project implements a shopping agent system using CrewAI's multi-agent architecture. The system consists of three specialized agents working together to provide a complete shopping experience:

1. **Orchestrator Agent**: Manages the conversation flow, understands user intent, and coordinates between the other agents
2. **Catalog Agent**: Searches and retrieves product information from an Excel database
3. **Cart Agent**: Handles the shopping cart operations and checkout process

## Features

- Natural language interaction with the shopping system
- Product search and retrieval from local Excel knowledge base
- Product recommendations based on user preferences
- Shopping cart management (add/remove items)
- Checkout process with user details collection
- Order confirmation with details saved to CSV and TXT files

## Technologies Used

- Python 3.8+
- CrewAI framework for multi-agent architecture
- pandas for data manipulation
- openpyxl for Excel file operations
- CSV and TXT file handling for order management
- Natural language processing for user intent understanding
- Agent-based architecture with specialized roles
- Local database integration via Excel

## How It Works

1. **Conversation Flow**:
   - The Orchestrator Agent greets the user and understands their shopping intent
   - User requests are analyzed and routed to the appropriate specialized agent

2. **Product Search**:
   - The Catalog Agent searches the Excel database for matching products
   - Results are formatted and presented to the user with options

3. **Cart Management**:
   - Users can select products to add to their cart
   - The Cart Agent tracks selected items and quantities

4. **Checkout Process**:
   - The Cart Agent collects delivery and payment information
   - Order details are saved to CSV and TXT files
   - Order confirmation is presented to the user

## Example Interaction

```
Agent: Hi! I'm your shopping assistant. How can I help you today?
User: I'm looking for a laptop.
Agent: I'd be happy to help you find a laptop. Could you tell me what specifications or features you're looking for?
User: I need one with at least 16GB RAM and an i7 processor.
Agent: I found 3 laptops matching your criteria:
1. Dell XPS 15 - i7, 16GB RAM, 512GB SSD - $1,299
2. HP Spectre x360 - i7, 16GB RAM, 1TB SSD - $1,499
3. Lenovo ThinkPad X1 - i7, 32GB RAM, 1TB SSD - $1,799
Which one would you like to know more about or add to your cart?
User: I'll take the Dell XPS 15.
Agent: Great choice! I've added the Dell XPS 15 to your cart. Would you like to continue shopping or proceed to checkout?
User: Let's checkout.
Agent: Please provide the following information to complete your order:
...
```
