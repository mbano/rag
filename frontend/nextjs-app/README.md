# RAG Frontend - Next.js Application

A simple and elegant frontend for the RAG (Retrieval-Augmented Generation) backend built with Next.js, TypeScript, and Tailwind CSS.

## Features

- Clean, modern chat interface
- Real-time message display
- Dark mode support
- Responsive design
- Loading states and error handling
- Auto-scroll to latest messages
- Support for local and remote backend APIs

## Prerequisites

- Node.js 18+ installed
- Backend API running (locally or remotely)

## Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Backend API URL

#### For Local Development (with local backend):
Create a `.env.local` file:

```bash
cp .env.example .env.local
```

The default configuration points to `http://localhost:8000`.

#### For Remote Backend (AWS or other cloud):
Create or edit `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://your-aws-endpoint.com
```

**Example with your AWS endpoint:**
```bash
NEXT_PUBLIC_API_URL=http://rag-app-alb-459149500.eu-north-1.elb.amazonaws.com
```

### 3. Run the Development Server

```bash
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000)

### 4. Build for Production

```bash
npm run build
npm start
```

## Important: Backend CORS Configuration

When using a remote backend, ensure your backend's CORS configuration allows requests from your frontend origin.

### For Development (frontend on localhost:3000):

Your backend's `app/main.py` should include:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### For Production Deployment:

If you deploy the frontend to a production domain (e.g., `https://myapp.com`), add that origin to the backend CORS configuration:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://myapp.com",  # Add your production frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Important:** After updating CORS configuration:
- If running backend locally: restart the server
- If running in Docker: rebuild the Docker image
- If running on AWS: redeploy the backend service

## Usage

1. Make sure your backend is running and accessible at the configured URL
2. Open the frontend in your browser (http://localhost:3000)
3. Type your question in the input field at the bottom
4. Press Send or hit Enter to submit your question
5. The assistant will display the response from your RAG system

## Backend API Requirements

The frontend expects the backend to have the following endpoint:

**POST** `/ask`

Request body:
```json
{
  "question": "Your question here"
}
```

Response:
```json
{
  "answer": "The assistant's response",
  ...other fields are optional
}
```

## Customization

### Displaying Additional Response Fields

To display more fields from the backend response (beyond just "answer"), edit `app/page.tsx`:

1. **Update the Message interface** (around line 5):
```typescript
interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string[];      // Add fields you want to display
  metadata?: any;
}
```

2. **Capture additional fields** from the response (around line 47):
```typescript
const data = await response.json();
const assistantMessage: Message = {
  role: "assistant",
  content: data.answer || "No answer received",
  sources: data.sources || [],  // Capture additional fields
  metadata: data.metadata,
};
```

3. **Display the fields** in the UI (around line 157):
```typescript
<p className="text-sm whitespace-pre-wrap break-words">
  {message.content}
</p>

{/* Display sources */}
{message.sources && message.sources.length > 0 && (
  <div className="mt-2 text-xs">
    <p className="font-semibold">Sources:</p>
    <ul className="list-disc ml-4">
      {message.sources.map((source, idx) => (
        <li key={idx}>{source}</li>
      ))}
    </ul>
  </div>
)}
```

### Styling

The app uses Tailwind CSS for styling. You can customize colors, spacing, and other design elements in:
- `tailwind.config.ts` - Tailwind configuration
- `app/globals.css` - Global styles and CSS variables

## Project Structure

```
frontend/nextjs-app/
├── app/
│   ├── globals.css      # Global styles
│   ├── layout.tsx       # Root layout
│   └── page.tsx         # Main chat page (API integration here)
├── public/              # Static assets (if needed)
├── .env.local           # Environment variables (create this)
├── .env.example         # Environment variables example
├── next.config.ts       # Next.js configuration
├── tailwind.config.ts   # Tailwind CSS configuration
├── tsconfig.json        # TypeScript configuration
└── package.json         # Dependencies
```

## Troubleshooting

### Backend Connection Issues

**Error: "Please make sure the backend server is running"**

1. **Check backend is accessible:**
   ```bash
   curl http://your-backend-url/
   ```
   Should return: `{"message":"status OK"}`

2. **Verify CORS configuration** on the backend:
   ```bash
   curl -H "Origin: http://localhost:3000" \
        -H "Access-Control-Request-Method: POST" \
        -X OPTIONS -i \
        http://your-backend-url/ask
   ```
   Should return `200 OK` with CORS headers.

3. **Check the URL in `.env.local`:**
   - Make sure there are no trailing slashes
   - Verify the protocol (http vs https)
   - Ensure the port is correct (if applicable)

4. **Backend CORS not configured:**
   - See "Backend CORS Configuration" section above
   - Remember to restart/rebuild/redeploy after CORS changes

### TypeScript Errors

The TypeScript errors shown in the editor will resolve once you run `npm install`.

### Network Errors in Browser Console

1. Open browser DevTools (F12)
2. Go to Network tab
3. Try sending a message
4. Check the failed request details for specific error messages

Common causes:
- Backend not running or unreachable
- CORS not properly configured
- Wrong URL in `.env.local`
- Firewall or security group blocking the connection

## Deployment Options

### Vercel (Recommended for Next.js)
```bash
npm install -g vercel
vercel
```
Set the `NEXT_PUBLIC_API_URL` environment variable in Vercel dashboard.

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

### AWS Amplify / Netlify / Other Platforms
Follow their Next.js deployment guides and set the `NEXT_PUBLIC_API_URL` environment variable.

## License

This project is part of the RAG application suite.
