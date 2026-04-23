export interface Product {
  _id: string;
  name: string;
  description: string;
  price: number;
  category: string;
  subcategory: string;

  images: string[];
  ratings: number;
  tags?: string[];
  attributes?: {
    color?: string;
    material?: string;
    size_available?: string[];
  };
  available_stores?: Array<{
    store_id: string;
    stock: number;
  }>;
  created_at?: string;

  stock?: number;
  featured?: boolean;
}
