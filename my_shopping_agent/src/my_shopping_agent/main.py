#!/usr/bin/env python
from crewai.flow.flow import Flow, listen, start
from crewai import Task
from my_shopping_agent.crews.poem_crew.Shopping_crew import ShopCrew, excel_source
from datetime import datetime
import re
import json
import pandas as pd
from pathlib import Path
import traceback
import csv



class ShopFlow(Flow):
    """Flow for the shopping application."""
    
    def __init__(self):
        super().__init__()
        # Initialize ShopCrew
        self.shop_crew = ShopCrew()
        self.orchestrator_agent = self.shop_crew.Orchestrator()
        self.catalog_agent = self.shop_crew.Catalog()
        self.knowledge_sources = [excel_source]
        self.cart_agent = self.shop_crew.Cart()
    
    @start()
    def interaction_with_user(self):
        """Get the user's shopping query."""
        print("Welcome to our Agentic AI Shopping Mart!")
        user_input = input("What would you like to shop for today? ")
        return user_input
        
    @listen(interaction_with_user)
    def extract_shopping_details(self, user_input):
        """Extract shopping details from the user query."""
        print("Analyzing your shopping needs...")
        print("Extracting details...")
        
        # Create task for the Orchestrator agent
        extract_task = Task(
            description=f"""
            Extract shopping details from this query: "{user_input}"
            
            Extract the following information:
            1. Product name (required)
            2. Price or price range (required)
            3. Product ID (optional)
            4. Quality (optional)
            
            Format your response as JSON with these fields:
            - product_name
            - price (number or range like "10-20")
            - pd_id (if available)
            - quality (if available)
            - is_valid (true if required fields are present)
            """,
            expected_output="json",
            agent=self.orchestrator_agent
        )
        
        # Execute the task
        result = self.orchestrator_agent.execute_task(extract_task)
        
        # Parse JSON result
        try:
            # Try to extract JSON using regex
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```|{[\s\S]*}', result)
            if json_match:
                json_str = json_match.group(1) if json_match.group(1) else json_match.group(0)
                shopping_details = json.loads(json_str)
            else:
                # Fallback: create basic structure
                shopping_details = {
                    'product_name': None,
                    'price': None,
                    'pd_id': None,
                    'quality': None,
                    'is_valid': False
                }
                
                # Try to extract product name
                name_match = re.search(r'(?:looking for|want to buy|need|interested in)\s+(?:a|an|the)?\s+([a-zA-Z0-9\s]+?)(?:\s+(?:for|with|that|in|at|of|by|quality|price|costs?))', user_input, re.IGNORECASE)
                if name_match:
                    shopping_details['product_name'] = name_match.group(1).strip()
                
                # Try to extract price
                price_match = re.search(r'(?:price|cost|for)[:\s]*\$?(\d+(?:\.\d+)?)', user_input, re.IGNORECASE)
                if price_match:
                    shopping_details['price'] = float(price_match.group(1))
                
                # Mark as valid if we have product name and price
                if shopping_details['product_name'] and shopping_details['price']:
                    shopping_details['is_valid'] = True
        
        except Exception as e:
            print(f"Error parsing extraction result: {str(e)}")
            shopping_details = {
                'product_name': "unknown product",
                'price': "market price",
                'pd_id': None,
                'quality': None,
                'is_valid': False
            }
        
        print(f"Extracted shopping details: {json.dumps(shopping_details, indent=2)}")
        return shopping_details
    
    @listen(extract_shopping_details)
    def search_product_catalog(self, shopping_details):
        """Find matching products using the Catalog agent."""
        print("Searching product catalog for matching items...")
        
        # Extract search parameters
        product_name = shopping_details.get('product_name', '').lower()
        price = shopping_details.get('price', '')
        pd_id = shopping_details.get('pd_id', '')
        quality = shopping_details.get('quality', '')
        
        # Build search criteria for logging
        search_criteria = []
        if product_name and product_name != "unknown product":
            search_criteria.append(f"Product: {product_name}")
        if price and price != "market price":
            if isinstance(price, float):
                search_criteria.append(f"Price: around ${price}")
            elif isinstance(price, str) and "-" in price:
                search_criteria.append(f"Price range: ${price}")
        if pd_id:
            search_criteria.append(f"Product ID: {pd_id}")
        if quality:
            search_criteria.append(f"Quality: {quality}")
        
        if search_criteria:
            print(f"Searching with criteria: {', '.join(search_criteria)}")
        else:
            print("Searching with no specific criteria")
        
        try:
            # Define task for the Catalog agent
            search_query = {
                "product_name": product_name,
                "price": price,
                "product_id": pd_id,
                "quality": quality,
                "search_criteria": ", ".join(search_criteria) if search_criteria else "No specific criteria"
            }
            
            search_criteria_text = json.dumps(search_query, indent=2)
            task_description = f"""
            Search the product catalog for items matching these criteria:
            {search_criteria_text}

            For each product, calculate a match score based on:
            1. Product name similarity (50 points max)
            2. Price match (40 points max)
            3. Quality match (10 points max)
            
            ONLY return products with a match score of 60 or higher.
            If no products meet this threshold, return an empty products array.
            
            Return a maximum of 3 matches with detailed reasoning for each match.
            Format your response as JSON with products array, each containing:
            - product_id
            - product_name
            - price
            - quality
            - in_stock (default to true)
            - description
            - match_score
            - reasoning
            
            Also include a search_summary field with a brief analysis of the results.
            """
            
            search_task = Task(
                description=task_description,
                expected_output="json",
                agent=self.catalog_agent,
                knowledge_sources=self.knowledge_sources
            )
            
            # Execute search task
            result = self.catalog_agent.execute_task(search_task)
            
            # Parse the agent's response
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```|{[\s\S]*}', result)
            if json_match:
                json_str = json_match.group(1) if json_match.group(1) else json_match.group(0)
                try:
                    matching_products = json.loads(json_str)
                except json.JSONDecodeError:
                    # Try to fix common JSON issues
                    fixed_json = re.sub(r',\s*}', '}', json_str)
                    fixed_json = re.sub(r',\s*]', ']', fixed_json)
                    try:
                        matching_products = json.loads(fixed_json)
                    except json.JSONDecodeError:
                        matching_products = self._fallback_parsing(result)
            else:
                matching_products = self._fallback_parsing(result)
            
            # Ensure expected structure
            if not isinstance(matching_products, dict):
                matching_products = {"products": [], "search_summary": "No matching products found"}
            if "products" not in matching_products:
                matching_products["products"] = []
            if "search_summary" not in matching_products:
                matching_products["search_summary"] = f"Found {len(matching_products.get('products', []))} matching products"
            
            # Filter out products with match score below 60 (as a safeguard)
            if "products" in matching_products:
                matching_products["products"] = [
                    product for product in matching_products["products"] 
                    if product.get("match_score", 0) >= 60
                ]
                matching_products["search_summary"] = f"Found {len(matching_products['products'])} matching products with score >= 60"
            
            # Print search results summary
            if matching_products["products"]:
                print(f"Found {len(matching_products['products'])} matching products")
                for idx, product in enumerate(matching_products["products"], 1):
                    print(f"Match #{idx}: {product.get('product_name')} - ${product.get('price')} " +
                          f"(Match score: {product.get('match_score', 'N/A')})")
                
                # Present product options
                self._present_product_options(matching_products)
            else:
                print("No matching products found in catalog")
                suggestions = []
                # Generate suggestions based on the catalog
                if product_name and product_name != "unknown product":
                    # Add suggestions feature
                    suggestions_task = Task(
                        description=f"""
                        The user searched for "{product_name}" but we found no matches.
                        Provide 3-5 alternative product suggestions that might be similar.
                        Format your response as a simple JSON array of product names.
                        """,
                        expected_output="json",
                        agent=self.catalog_agent,
                        knowledge_sources=self.knowledge_sources
                    )
                    suggestions_result = self.catalog_agent.execute_task(suggestions_task)
                    try:
                        suggestions_match = re.search(r'```json\s*([\s\S]*?)\s*```|\[[\s\S]*\]', suggestions_result)
                        if suggestions_match:
                            suggestions_str = suggestions_match.group(1) if suggestions_match.group(1) else suggestions_match.group(0)
                            suggestions = json.loads(suggestions_str)
                    except:
                        suggestions = []
                
                matching_products["suggestions"] = suggestions
                if suggestions:
                    print(f"You might be interested in: {', '.join(suggestions)}")
                print("Would you like to refine your search criteria?")
            
            # Return structured result
            result = {
                "original_query": shopping_details,
                "matching_products": matching_products,
                "search_timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            print(f"Error searching product catalog: {str(e)}")
            print(traceback.format_exc())
            
            return {
                "original_query": shopping_details,
                "matching_products": {
                    "products": [],
                    "search_summary": f"Search failed: {str(e)}"
                },
                "search_timestamp": datetime.now().isoformat(),
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _fallback_parsing(self, result_text):
        """Fallback method to extract product information when JSON parsing fails."""
        products = []
        
        # Try to find product blocks using regex
        product_blocks = re.findall(r'Product\s*(?:ID|#)?:?\s*(\d+).*?Product Name:?\s*([^\n]+).*?Price:?\s*\$?(\d+(?:\.\d+)?)', 
                                   result_text, re.DOTALL)
        
        for prod_id, name, price in product_blocks:
            # Try to extract quality
            quality_match = re.search(r'Quality:?\s*([^\n]+)', result_text)
            quality = quality_match.group(1).strip() if quality_match else "Standard"
            
            # Try to extract match score
            score_match = re.search(r'Match Score:?\s*(\d+)', result_text)
            match_score = int(score_match.group(1)) if score_match else 50
            
            # Only include products with match score >= 60
            if match_score >= 60:
                products.append({
                    "product_id": prod_id.strip(),
                    "product_name": name.strip(),
                    "price": float(price),
                    "quality": quality,
                    "in_stock": True,
                    "description": "High quality product", 
                    "match_score": match_score,
                    "reasoning": "Product matches search criteria"
                })
        
        # Extract summary if available
        summary_match = re.search(r'Summary:?\s*([^\n]+)', result_text)
        search_summary = summary_match.group(1).strip() if summary_match else f"Found {len(products)} matching products"
        
        return {
            "products": products,
            "search_summary": search_summary
        }
    
    def _present_product_options(self, matching_products):
        """Present product options to the user and handle selection."""
        if not matching_products.get("products"):
            return None
        
        print("\n=== Product Options ===")
        for idx, product in enumerate(matching_products["products"], 1):
            print(f"\n[{idx}] {product['product_name']}")
            print(f"    Price: ${product['price']}")
            print(f"    Quality: {product['quality']}")
            print(f"    Description: {product['description']}")
            print(f"    In Stock: {'Yes' if product['in_stock'] else 'No'}")
            print(f"    Match Score: {product['match_score']}")
            print(f"    Why This Match: {product['reasoning']}")
        
        print("\n[R] Refine search")
        print("[Q] Quit search")
        
        # Get user selection
        while True:
            choice = input("\nSelect an option (1-3, R, Q): ").strip().upper()
            
            if choice == 'Q':
                print("Ending search. Thank you for shopping with us!")
                return {"action": "quit"}
            
            elif choice == 'R':
                print("Let's refine your search.")
                refined_query = input("Please provide more specific details: ")
                return {
                    "action": "refine",
                    "refined_query": refined_query
                }
            
            elif choice.isdigit() and 1 <= int(choice) <= len(matching_products["products"]):
                selected_idx = int(choice) - 1
                selected_product = matching_products["products"][selected_idx]
                print(f"\nYou selected: {selected_product['product_name']}")
                print("Great choice! Adding to cart...")
                
                return {
                    "action": "select",
                    "selected_product": selected_product
                }
            
            else:
                print("Invalid selection. Please try again.")
    
    @listen(search_product_catalog)
    def handle_product_selection(self, search_results):
        """Handle the next steps after product search results."""
        if not search_results or "error" in search_results:
            print("Sorry, we encountered an issue with your search.")
            return {"status": "failed", "reason": "search_error"}
        
        matching_products = search_results.get("matching_products", {})
        products = matching_products.get("products", [])
        
        if not products:
            print("No products matched your search criteria.")
            refine_search = input("Would you like to refine your search? (y/n): ").strip().lower()
            if refine_search == 'y':
                new_query = input("Please provide more details for your search: ")
                return {
                    "status": "refine",
                    "new_query": new_query,
                    "original_search": search_results.get("original_query")
                }
            else:
                print("Thank you for using our shopping assistant. Have a great day!")
                return {"status": "ended", "reason": "no_products_found"}
        
        # Let the user select a product
        selection = self._present_product_options(matching_products)
        
        if selection and selection.get("action") == "select":
            selected_product = selection.get("selected_product")
            
            # Check stock availability
            if not selected_product.get("in_stock", True):
                print(f"We're sorry, but {selected_product['product_name']} is currently out of stock.")
                print("Would you like to be notified when it becomes available?")
                notify = input("Enter 'y' for yes or 'n' for no: ").strip().lower()
                
                if notify == 'y':
                    email = input("Please enter your email address: ")
                    print(f"Thank you! We'll notify you at {email} when {selected_product['product_name']} is back in stock.")
                    return {
                        "status": "notification_set",
                        "product": selected_product,
                        "email": email
                    }
                else:
                    print("Would you like to select a different product?")
                    try_again = input("Enter 'y' for yes or 'n' for no: ").strip().lower()
                    if try_again == 'y':
                        return self.handle_product_selection(search_results)
                    else:
                        print("Thank you for using our shopping assistant. Have a great day!")
                        return {"status": "ended", "reason": "product_out_of_stock"}
            
            # Process purchase
            print(f"\nProcessing purchase for: {selected_product['product_name']}")
            print(f"Price: ${selected_product['price']}")
            
            # Confirm purchase
            confirm = input("\nWould you like to proceed with this purchase? (y/n): ").strip().lower()
            if confirm == 'y':
                # Collect shipping information
                print("\nPlease provide shipping information:")
                name = input("Full Name: ")
                address = input("Shipping Address: ")
                phone = input("Contact Phone: ")
                
                # Collect payment information
                print("\nPlease provide payment information:")
                card_type = input("Card Type (Visa/Mastercard/etc.): ")
                card_number = input("Card Number: ")
                
                # Use Cart agent to process the order
                cart_task_description = f"""
                Process this purchase:
                - Product: {selected_product['product_name']}
                - Product ID: {selected_product['product_id']}
                - Price: ${selected_product['price']}
                - Quality: {selected_product['quality']}
                
                Customer information:
                - Name: {name}
                - Address: {address}
                - Phone: {phone}
                - Payment: {card_type} card
                
                Generate an order confirmation with:
                1. A unique order ID
                2. Purchase details
                3. Shipping information
                4. Estimated delivery date (5-7 business days from now)
                
                Format response as JSON with:
                - order_id
                - product (object with all product details)
                - customer (object with customer details)
                - payment_status
                - shipping_status
                - estimated_delivery
                """

                cart_task = Task(
                    description=cart_task_description,
                    expected_output="json",
                    agent=self.cart_agent
                )
                
                # Execute cart task
                cart_result = self.cart_agent.execute_task(cart_task)
                
                # Parse the JSON response
                try:
                    json_match = re.search(r'```json\s*([\s\S]*?)\s*```|{[\s\S]*}', cart_result)
                    if json_match:
                        json_str = json_match.group(1) if json_match.group(1) else json_match.group(0)
                        order_info = json.loads(json_str)
                    else:
                        # Fallback order_info
                        order_id = f"ORD-{hash(selected_product['product_name'] + str(datetime.now()))}"
                        order_info = {
                            "order_id": order_id,
                            "product": selected_product,
                            "customer": {
                                "name": name,
                                "address": address,
                                "phone": phone
                            },
                            "payment_status": "completed",
                            "shipping_status": "processing",
                            "estimated_delivery": (datetime.now() + pd.Timedelta(days=7)).strftime("%Y-%m-%d")
                        }
                except Exception as e:
                    print(f"Error processing order: {str(e)}")
                    # Fallback order_info
                    order_id = f"ORD-{hash(selected_product['product_name'] + str(datetime.now()))}"
                    order_info = {
                        "order_id": order_id,
                        "product": selected_product,
                        "customer": {
                            "name": name,
                            "address": address,
                            "phone": phone
                        },
                        "payment_status": "completed",
                        "shipping_status": "processing",
                        "estimated_delivery": (datetime.now() + pd.Timedelta(days=7)).strftime("%Y-%m-%d")
                    }
                
                # Display order confirmation
                print("\n" + "="*50)
                print(f"ORDER CONFIRMATION - {order_info.get('order_id', 'N/A')}")
                print("="*50)
                print(f"Thank you for your purchase, {name}!")
                print(f"Your {selected_product['product_name']} will be shipped to:")
                print(f"{address}")
                print(f"\nEstimated delivery: {order_info.get('estimated_delivery', 'N/A')}")
                print(f"Payment status: {order_info.get('payment_status', 'completed')}")
                print("="*50)
                
                # Return order information
                return {
                    "status": "purchase_complete",
                    "order_id": order_info.get("order_id"),
                    "product": selected_product,
                    "customer": {
                        "name": name,
                        "address": address,
                        "phone": phone
                    },
                    "payment_status": order_info.get("payment_status", "completed"),
                    "shipping_status": order_info.get("shipping_status", "processing"),
                    "estimated_delivery": order_info.get("estimated_delivery"),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print("Purchase cancelled.")
                print("Would you like to select a different product?")
                try_again = input("Enter 'y' for yes or 'n' for no: ").strip().lower()
                if try_again == 'y':
                    return self.handle_product_selection(search_results)
                else:
                    print("Thank you for using our shopping assistant. Have a great day!")
                    return {"status": "ended", "reason": "purchase_cancelled"}
                
        elif selection and selection.get("action") == "refine":
            refined_query = selection.get("refined_query")
            print(f"Refining search with: {refined_query}")
            
            return {
                "status": "refine",
                "new_query": refined_query,
                "original_search": search_results.get("original_query")
            }
        
        elif selection and selection.get("action") == "quit":
            print("Thank you for using our shopping assistant. Have a great day!")
            return {"status": "ended", "reason": "user_quit"}
        
        else:
            print("No selection was made. Would you like to search for something else?")
            new_search = input("Enter 'y' for yes or 'n' for no: ").strip().lower()
            if new_search == 'y':
                new_query = input("What would you like to search for? ")
                return {
                    "status": "new_search",
                    "new_query": new_query
                }
            else:
                print("Thank you for using our shopping assistant. Have a great day!")
                return {"status": "ended", "reason": "no_selection"}
    
    @listen(handle_product_selection)
    def save_cart_to_file(self, selection_result):
        """Save selected products to a cart file."""
        print("Attempting to save cart to file...")

        if not selection_result or selection_result.get("status") != "purchase_complete":
            print("No purchase to save - skipping cart update")
            return {
                "cart_update": "skipped",
                "reason": "No product was purchased"
            }
            
        # Use the Cart agent to save the purchase
        cart_save_task = f"""
        Save this purchase to the shopping cart files:
        
        Order ID: {selection_result.get('order_id', 'Unknown')}
        Product: {selection_result.get('product', {}).get('product_name', 'Unknown')}
        Product ID: {selection_result.get('product', {}).get('product_id', 'Unknown')}
        Price: ${selection_result.get('product', {}).get('price', 0)}
        Quality: {selection_result.get('product', {}).get('quality', 'Standard')}
        
        Customer:
        Name: {selection_result.get('customer', {}).get('name', 'Unknown')}
        Address: {selection_result.get('customer', {}).get('address', 'Unknown')}
        Phone: {selection_result.get('customer', {}).get('phone', 'Unknown')}
        
        Create both CSV and TXT files in the shopping_cart directory with timestamp.
        Confirm when the files have been created and provide the file paths.
        """
        
        try:
            # Execute the cart save task
            cart_save_task_obj = Task(
                description=cart_save_task,
                expected_output="text",
                agent=self.cart_agent
            )

            cart_save_result = self.cart_agent.execute_task(cart_save_task_obj)
            
            # Ensure shopping_cart directory exists
            cart_dir = Path("shopping_cart")
            cart_dir.mkdir(exist_ok=True)
            
            # Generate filenames with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            order_id = selection_result.get('order_id', 'order').replace("-", "_")
            
            csv_filename = cart_dir / f"cart_{order_id}_{timestamp}.csv"
            txt_filename = cart_dir / f"cart_{order_id}_{timestamp}.txt"
            
            # Write to CSV file
            with open(csv_filename, 'w', newline='') as csvfile:
                fieldnames = ['order_id', 'product_name', 'product_id', 'price', 'quality', 
                             'customer_name', 'customer_address', 'customer_phone', 
                             'payment_status', 'shipping_status', 'estimated_delivery']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerow({
                    'order_id': selection_result.get('order_id', 'Unknown'),
                    'product_name': selection_result.get('product', {}).get('product_name', 'Unknown'),
                    'product_id': selection_result.get('product', {}).get('product_id', 'Unknown'),
                    'price': selection_result.get('product', {}).get('price', 0),
                    'quality': selection_result.get('product', {}).get('quality', 'Standard'),
                    'customer_name': selection_result.get('customer', {}).get('name', 'Unknown'),
                    'customer_address': selection_result.get('customer', {}).get('address', 'Unknown'),
                    'customer_phone': selection_result.get('customer', {}).get('phone', 'Unknown'),
                    'payment_status': selection_result.get('payment_status', 'completed'),
                    'shipping_status': selection_result.get('shipping_status', 'processing'),
                    'estimated_delivery': selection_result.get('estimated_delivery', 'Unknown')
                })
            
            # Write to TXT file
            with open(txt_filename, 'w') as txtfile:
                txtfile.write(f"ORDER CONFIRMATION - {selection_result.get('order_id', 'Unknown')}\n")
                txtfile.write("="*50 + "\n")
                txtfile.write(f"Purchase Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                txtfile.write("PRODUCT DETAILS:\n")
                txtfile.write(f"Product: {selection_result.get('product', {}).get('product_name', 'Unknown')}\n")
                txtfile.write(f"Product ID: {selection_result.get('product', {}).get('product_id', 'Unknown')}\n")
                txtfile.write(f"Price: ${selection_result.get('product', {}).get('price', 0)}\n")
                txtfile.write(f"Quality: {selection_result.get('product', {}).get('quality', 'Standard')}\n\n")
                txtfile.write("CUSTOMER INFORMATION:\n")
                txtfile.write(f"Name: {selection_result.get('customer', {}).get('name', 'Unknown')}\n")
                txtfile.write(f"Address: {selection_result.get('customer', {}).get('address', 'Unknown')}\n")
                txtfile.write(f"Phone: {selection_result.get('customer', {}).get('phone', 'Unknown')}\n\n")
                txtfile.write("ORDER STATUS:\n")
                txtfile.write(f"Payment Status: {selection_result.get('payment_status', 'completed')}\n")
                txtfile.write(f"Shipping Status: {selection_result.get('shipping_status', 'processing')}\n")
                txtfile.write(f"Estimated Delivery: {selection_result.get('estimated_delivery', 'Unknown')}\n")
                txtfile.write("="*50 + "\n")
                txtfile.write("Thank you for shopping with us!\n")
            
            print(f"Cart saved successfully!")
            print(f"CSV File: {csv_filename}")
            print(f"TXT File: {txt_filename}")
            
            return {
                "cart_update": "success",
                "csv_file": str(csv_filename),
                "txt_file": str(txt_filename),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error saving cart to file: {str(e)}")
            traceback.print_exc()
            
            return {
                "cart_update": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }
        
    @listen(save_cart_to_file)
    def complete_shopping_session(self, cart_result):
        """Complete the shopping session and provide summary."""
        print("\n" + "="*50)
        print("SHOPPING SESSION COMPLETE")
        print("="*50)
        
        if cart_result.get("cart_update") == "success":
            print("Your order has been processed successfully!")
            print(f"Order saved to files:")
            print(f"- CSV: {cart_result.get('csv_file')}")
            print(f"- TXT: {cart_result.get('txt_file')}")
        elif cart_result.get("cart_update") == "failed":
            print("Your order was processed, but there was an issue saving the receipt.")
            print(f"Error: {cart_result.get('error', 'Unknown error')}")
        else:
            print("Your shopping session has ended.")
            print(f"Status: {cart_result.get('cart_update', 'No purchase made')}")
            print(f"Reason: {cart_result.get('reason', 'N/A')}")
        
        # Ask if user wants to continue shopping
        continue_shopping = input("\nWould you like to shop for something else? (y/n): ").strip().lower()
        
        if continue_shopping == 'y':
            print("\nStarting a new shopping session...")
            # Restart the flow
            return self.interaction_with_user()
        else:
            print("\nThank you for shopping with us! Have a great day!")
            return {
                "session_status": "completed",
                "timestamp": datetime.now().isoformat(),
                "cart_result": cart_result
            }
        


def kickoff():
    shop_flow = ShopFlow()
    shop_flow.kickoff()


def plot():
    shop_flow = ShopFlow()
    shop_flow.plot()


if __name__ == "__main__":
    kickoff()
          
        