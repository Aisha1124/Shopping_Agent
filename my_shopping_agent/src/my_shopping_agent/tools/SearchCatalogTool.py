# from typing import Type, List, Optional
# import pandas as pd
# import os
# from crewai.tools import BaseTool
# from pydantic import BaseModel, Field


# class ProductSearchInput(BaseModel):
#     """Input schema for ProductCatalogTool."""
    
#     query: str = Field(..., description="Search query or keywords to find products.")
#     category: Optional[str] = Field(None, description="Optional category to filter products.")
#     max_price: Optional[float] = Field(None, description="Maximum price filter.")
#     min_price: Optional[float] = Field(None, description="Minimum price filter.")
#     sort_by: Optional[str] = Field(None, description="Sort results by: 'price_asc', 'price_desc', or 'name'.")
#     limit: Optional[int] = Field(10, description="Maximum number of results to return.")


# class ProductCatalogTool(BaseTool):
#     name: str = "product_catalog_search"
#     description: str = (
#         "Search for products in the catalog based on keywords, category, and price range. "
#         "This tool searches the product catalog Excel file and returns matching products. "
#         "You can filter by category, price range, and sort the results."
#     )
#     args_schema: Type[BaseModel] = ProductSearchInput
    
#     def __init__(self, catalog_file: str = "product_catalog.xlsx"):
#         """Initialize the ProductCatalogTool with the catalog file path."""
#         super().__init__()
#         self.catalog_file = catalog_file
        
#     def _load_catalog(self) -> pd.DataFrame:
#         """Load the product catalog from Excel file."""
#         if not os.path.exists(self.catalog_file):
#             raise FileNotFoundError(f"Product catalog file not found: {self.catalog_file}")
        
#         try:
#             # Assuming the Excel file has columns: pd_id, product_name, quality, price
#             df = pd.read_excel(self.catalog_file)
#             return df
#         except Exception as e:
#             raise Exception(f"Error loading product catalog: {str(e)}")
    
#     def _run(
#         self, 
#         query: str, 
#         category: Optional[str] = None,
#         max_price: Optional[float] = None,
#         min_price: Optional[float] = None,
#         sort_by: Optional[str] = None,
#         limit: int = 10
#     ) -> str:
#         """
#         Search for products in the catalog based on the given criteria.
        
#         Args:
#             query: Search keywords
#             category: Optional category filter
#             max_price: Maximum price filter
#             min_price: Minimum price filter
#             sort_by: Sorting option ('price_asc', 'price_desc', 'name')
#             limit: Maximum number of results
            
#         Returns:
#             Formatted string with search results
#         """
#         try:
#             # Load the product catalog
#             df = self._load_catalog()
            
#             # Filter by search query in product name
#             mask = df['product_name'].str.contains(query, case=False, na=False)
            
#             # Apply category filter if provided
#             if category:
#                 # Assuming there's a 'category' column - adjust if your Excel has a different column
#                 if 'category' in df.columns:
#                     category_mask = df['category'].str.contains(category, case=False, na=False)
#                     mask = mask & category_mask
            
#             # Apply price filters if provided
#             if min_price is not None:
#                 mask = mask & (df['price'] >= min_price)
                
#             if max_price is not None:
#                 mask = mask & (df['price'] <= max_price)
            
#             # Apply filters to get matching products
#             results = df[mask].copy()
            
#             # Sort results if requested
#             if sort_by:
#                 if sort_by == 'price_asc':
#                     results = results.sort_values('price', ascending=True)
#                 elif sort_by == 'price_desc':
#                     results = results.sort_values('price', ascending=False)
#                 elif sort_by == 'name':
#                     results = results.sort_values('product_name', ascending=True)
            
#             # Limit results
#             results = results.head(limit)
            
#             # Format the results
#             if len(results) == 0:
#                 return "No products found matching your criteria."
            
#             formatted_results = "Found the following products:\n\n"
#             for _, row in results.iterrows():
#                 formatted_results += f"ID: {row['pd_id']}\n"
#                 formatted_results += f"Name: {row['product_name']}\n"
#                 formatted_results += f"Quality: {row['quality']}\n"
#                 formatted_results += f"Price: ${row['price']:.2f}\n"
#                 formatted_results += "-" * 30 + "\n"
            
#             return formatted_results
            
#         except Exception as e:
#             return f"Error searching product catalog: {str(e)}"


# class ProductDetailsInput(BaseModel):
#     """Input schema for getting detailed product information."""
    
#     product_id: str = Field(..., description="Product ID to get details for.")


# class ProductDetailsTool(BaseTool):
#     name: str = "product_details"
#     description: str = (
#         "Get detailed information about a specific product by its ID. "
#         "Use this when you need complete information about a particular product."
#     )
#     args_schema: Type[BaseModel] = ProductDetailsInput
    
#     def __init__(self, catalog_file: str = "product_catalog.xlsx"):
#         """Initialize the ProductDetailsTool with the catalog file path."""
#         super().__init__()
#         self.catalog_file = catalog_file
    
#     def _load_catalog(self) -> pd.DataFrame:
#         """Load the product catalog from Excel file."""
#         if not os.path.exists(self.catalog_file):
#             raise FileNotFoundError(f"Product catalog file not found: {self.catalog_file}")
        
#         try:
#             df = pd.read_excel(self.catalog_file)
#             return df
#         except Exception as e:
#             raise Exception(f"Error loading product catalog: {str(e)}")
    
#     def _run(self, product_id: str) -> str:
#         """
#         Get detailed product information by product ID.
        
#         Args:
#             product_id: The unique identifier of the product
            
#         Returns:
#             Formatted string with detailed product information
#         """
#         try:
#             # Load the product catalog
#             df = self._load_catalog()
            
#             # Find the product by ID
#             product = df[df['pd_id'] == product_id]
            
#             if len(product) == 0:
#                 return f"Product with ID '{product_id}' not found."
            
#             # Get the first matching product (assuming IDs are unique)
#             product = product.iloc[0]
            
#             # Format the detailed information
#             details = f"Product Details:\n\n"
#             details += f"ID: {product['pd_id']}\n"
#             details += f"Name: {product['product_name']}\n"
#             details += f"Quality: {product['quality']}\n"
#             details += f"Price: ${product['price']:.2f}\n"
            
#             # Add any additional columns if present
#             extra_columns = [col for col in product.index if col not in ['pd_id', 'product_name', 'quality', 'price']]
            
#             if extra_columns:
#                 details += "\nAdditional Information:\n"
#                 for col in extra_columns:
#                     details += f"{col.title()}: {product[col]}\n"
            
#             return details
            
#         except Exception as e:
#             return f"Error retrieving product details: {str(e)}"