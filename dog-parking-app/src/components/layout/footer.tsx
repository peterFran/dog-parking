import Link from 'next/link';
import { Dog } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-gray-50 border-t">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Logo and Description */}
          <div className="col-span-1 md:col-span-2">
            <Link href="/" className="flex items-center space-x-2 mb-4">
              <Dog className="h-8 w-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">Dog Parking</span>
            </Link>
            <p className="text-gray-600 mb-4">
              Premium dog care services including daycare, boarding, grooming, and training. 
              Find the perfect venue for your furry friend.
            </p>
          </div>

          {/* Services */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-4">
              Services
            </h3>
            <ul className="space-y-2">
              <li>
                <Link href="/venues?service=daycare" className="text-gray-600 hover:text-gray-900">
                  Dog Daycare
                </Link>
              </li>
              <li>
                <Link href="/venues?service=boarding" className="text-gray-600 hover:text-gray-900">
                  Dog Boarding
                </Link>
              </li>
              <li>
                <Link href="/venues?service=grooming" className="text-gray-600 hover:text-gray-900">
                  Dog Grooming
                </Link>
              </li>
              <li>
                <Link href="/venues?service=training" className="text-gray-600 hover:text-gray-900">
                  Dog Training
                </Link>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-4">
              Company
            </h3>
            <ul className="space-y-2">
              <li>
                <Link href="/about" className="text-gray-600 hover:text-gray-900">
                  About Us
                </Link>
              </li>
              <li>
                <Link href="/contact" className="text-gray-600 hover:text-gray-900">
                  Contact
                </Link>
              </li>
              <li>
                <Link href="/privacy" className="text-gray-600 hover:text-gray-900">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="text-gray-600 hover:text-gray-900">
                  Terms of Service
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-200 mt-8 pt-8">
          <p className="text-center text-gray-500 text-sm">
            © 2025 Dog Parking. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}