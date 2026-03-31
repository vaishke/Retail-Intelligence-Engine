export interface Product {
  _id: string;
  name: string;
  description: string;
  price: number;
  category: string;
  subcategory: string;

  images: string[];
  ratings: number;

  stock?: number;
  featured?: boolean;
}