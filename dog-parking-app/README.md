# Dog Parking - React Frontend

A modern React application built with Next.js for the Dog Parking platform, providing premium dog care services including daycare, boarding, grooming, and training.

## Features

- 🔐 **Firebase Authentication** - Secure user authentication and registration
- 🎨 **Modern UI** - Built with Tailwind CSS and custom components
- 📱 **Responsive Design** - Works perfectly on all devices
- ⚡ **Fast Performance** - Optimized with Next.js and React Query
- 🔄 **Real-time Data** - Integrated with Dog Parking API
- 🛡️ **Type Safety** - Full TypeScript support

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Authentication**: Firebase Auth
- **Data Fetching**: TanStack React Query
- **UI Components**: Custom components with Radix UI primitives
- **Icons**: Lucide React
- **Deployment**: Vercel

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Firebase project setup

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd dog-parking-app
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env.local
```

Edit `.env.local` with your Firebase configuration:
```env
NEXT_PUBLIC_FIREBASE_API_KEY=your-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=dog-parking-465416.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=dog-parking-465416
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=dog-parking-465416.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
NEXT_PUBLIC_FIREBASE_APP_ID=your-app-id
NEXT_PUBLIC_API_BASE_URL=https://f57ugwpt6j.execute-api.us-east-1.amazonaws.com/staging
```

4. Start the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── auth/              # Authentication pages
│   ├── venues/            # Venue-related pages
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Homepage
│   └── providers.tsx      # Context providers
├── components/            # Reusable components
│   ├── auth/              # Authentication components
│   ├── layout/            # Layout components
│   └── ui/                # UI components
├── contexts/              # React contexts
├── hooks/                 # Custom hooks
├── lib/                   # Utility libraries
├── types/                 # TypeScript type definitions
└── utils/                 # Utility functions
```

## Key Features

### Authentication
- User registration and login with Firebase
- Protected routes and authentication guards
- Email verification support
- Secure token management

### Venue Discovery
- Browse available dog care venues
- Filter by service type and location
- View detailed venue information
- Real-time availability checking

### User Dashboard
- Manage dog profiles
- View and manage bookings
- Update user preferences
- Booking history and status

### Responsive Design
- Mobile-first approach
- Adaptive layouts for all screen sizes
- Touch-friendly interactions
- Optimized performance

## API Integration

The app integrates with the Dog Parking API providing:

- **Public Endpoints**: Venue listings and details
- **Protected Endpoints**: User profiles, dog management, bookings
- **Authentication**: Firebase JWT token validation
- **Error Handling**: Comprehensive error states and retry logic

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript compiler

### Code Quality

- ESLint configuration for code quality
- TypeScript for type safety
- Prettier for code formatting
- Consistent component patterns

## Deployment

### Vercel (Recommended)

1. Connect your GitHub repository to Vercel
2. Configure environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

### Environment Variables for Vercel

Set these in your Vercel project settings:

- `NEXT_PUBLIC_FIREBASE_API_KEY`
- `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`
- `NEXT_PUBLIC_FIREBASE_PROJECT_ID`
- `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET`
- `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID`
- `NEXT_PUBLIC_FIREBASE_APP_ID`
- `NEXT_PUBLIC_API_BASE_URL`

### Manual Deployment

```bash
npm run build
npm run start
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.