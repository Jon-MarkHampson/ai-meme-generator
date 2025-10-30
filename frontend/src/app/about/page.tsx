import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import Link from "next/link"

export default function AboutPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="space-y-8">
        {/* Header Section */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold tracking-tight">About AI Meme Generator</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Create hilarious memes effortlessly with the power of artificial intelligence
          </p>
        </div>

        <Separator />

        {/* Main Content */}
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                AI-Powered Generation
              </CardTitle>
              <CardDescription>
                Intelligent meme creation at your fingertips
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Our advanced AI will help you craft the perfect meme text and help generate a matching image.
                Simply interact with the chatbot to describe what you want, search the web for inspiration,
                and watch as the AI crafts the perfect meme to match your idea.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Multiple AI Models
              </CardTitle>
              <CardDescription>
                Choose from different AI providers
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Select between OpenAI and Anthropic models for text generation to find the AI voice
                that best matches your humor style. For image generation, choose between OpenAI's
                GTP Image 1 and Google's Nano Banana. Each model brings its own unique approach to understanding
                context and generating creative meme content.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Interactive Chat
              </CardTitle>
              <CardDescription>
                Conversational meme creation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Engage in natural conversations with our AI to refine your memes. Provide feedback,
                request modifications, or explore different variations until you get the perfect
                meme for any situation.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Personal Gallery
              </CardTitle>
              <CardDescription>
                Save and organize your creations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Build your personal collection of AI-generated memes. Favorite the best ones,
                browse your creation history, and easily share your funniest moments with friends
                and social media.
              </p>
            </CardContent>
          </Card>
        </div>

        <Separator />

        {/* How It Works Section */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-center">How It Works</h2>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="text-center space-y-2">
              <div className="w-12 h-12 bg-primary text-primary-foreground rounded-full flex items-center justify-center mx-auto text-xl font-bold">
                1
              </div>
              <h3 className="font-semibold">Describe Your Idea</h3>
              <p className="text-sm text-muted-foreground">
                Tell our AI what kind of meme you want to create using natural language
              </p>
            </div>
            <div className="text-center space-y-2">
              <div className="w-12 h-12 bg-primary text-primary-foreground rounded-full flex items-center justify-center mx-auto text-xl font-bold">
                2
              </div>
              <h3 className="font-semibold">AI Magic Happens</h3>
              <p className="text-sm text-muted-foreground">
                Our AI helps perfect your meme text and generates a fitting image
              </p>
            </div>
            <div className="text-center space-y-2">
              <div className="w-12 h-12 bg-primary text-primary-foreground rounded-full flex items-center justify-center mx-auto text-xl font-bold">
                3
              </div>
              <h3 className="font-semibold">Share & Enjoy</h3>
              <p className="text-sm text-muted-foreground">
                Download your meme and share it with the world, or save it to your gallery
              </p>
            </div>
          </div>
        </div>

        <Separator />

        {/* CTA Section */}
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-bold">Ready to Create Some Memes?</h2>
          <p className="text-muted-foreground">
            Join thousands of users who are already creating hilarious content with AI
          </p>
          <div className="flex gap-4 justify-center">
            <Button asChild size="lg">
              <Link href="/generate">Start Creating</Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/gallery">View Gallery</Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}