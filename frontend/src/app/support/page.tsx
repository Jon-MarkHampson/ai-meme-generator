import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { Bug, GitBranch, HelpCircle, ExternalLink } from "lucide-react"

export default function SupportPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="space-y-8">
        {/* Header Section */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold tracking-tight">Support & Feedback</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Need help or found a bug? We're here to help improve your experience
          </p>
        </div>

        <Separator />

        {/* Main Support Options */}
        <div className="grid gap-6 md:grid-cols-2">
          <Card className="border-destructive/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bug className="h-5 w-5" />
                Report a Bug
              </CardTitle>
              <CardDescription>
                Found something that's not working correctly?
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Help us improve by reporting bugs directly on GitHub. Please include:
              </p>
              <ul className="text-sm text-muted-foreground space-y-2 list-disc list-inside">
                <li>A clear description of the issue</li>
                <li>Steps to reproduce the problem</li>
                <li>Expected vs. actual behavior</li>
                <li>Screenshots if applicable</li>
              </ul>
              <Button asChild className="w-full">
                <a
                  href="https://github.com/Jon-MarkHampson/ai-meme-generator/issues/new?labels=bug&template=bug_report.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2"
                >
                  Report Bug on GitHub
                  <ExternalLink className="h-4 w-4" />
                </a>
              </Button>
            </CardContent>
          </Card>

          <Card className="border-primary/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <GitBranch className="h-5 w-5" />
                Feature Request
              </CardTitle>
              <CardDescription>
                Have an idea to make this better?
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                We'd love to hear your suggestions! Submit a feature request including:
              </p>
              <ul className="text-sm text-muted-foreground space-y-2 list-disc list-inside">
                <li>Description of the feature</li>
                <li>Why it would be useful</li>
                <li>How you envision it working</li>
                <li>Any examples or mockups</li>
              </ul>
              <Button asChild variant="secondary" className="w-full">
                <a
                  href="https://github.com/Jon-MarkHampson/ai-meme-generator/issues/new?labels=enhancement&template=feature_request.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2"
                >
                  Request Feature on GitHub
                  <ExternalLink className="h-4 w-4" />
                </a>
              </Button>
            </CardContent>
          </Card>
        </div>

        <Separator />

        {/* General Help Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <HelpCircle className="h-5 w-5" />
              General Questions
            </CardTitle>
            <CardDescription>
              Need help using the AI Meme Generator?
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              For general questions or discussions about the project, you can:
            </p>
            <ul className="text-sm text-muted-foreground space-y-2 list-disc list-inside">
              <li>Check existing GitHub issues for similar questions</li>
              <li>Review the project documentation on GitHub</li>
              <li>Open a new discussion on the GitHub repository</li>
            </ul>
            <Button asChild variant="outline" className="w-full">
              <a
                href="https://github.com/Jon-MarkHampson/ai-meme-generator/issues"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2"
              >
                View All Issues & Discussions
                <ExternalLink className="h-4 w-4" />
              </a>
            </Button>
          </CardContent>
        </Card>

        <Separator />

        {/* FAQ Section */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-center">Common Questions</h2>
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Why isn't my meme generating?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Make sure you're logged in and have a stable internet connection.
                  If the issue persists, try refreshing the page or clearing your browser cache.
                  If you continue to experience issues, please report a bug.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Can I use the generated memes commercially?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Generated memes are for personal and educational use. Please review the
                  terms of service for each AI provider (OpenAI, Anthropic) regarding
                  commercial use of AI-generated content.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">How do I delete my account?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Currently, account deletion must be requested through a GitHub issue.
                  We're working on adding self-service account management features.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>

        <Separator />

        {/* Contributing Section */}
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-bold">Want to Contribute?</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            This is an open-source project! Contributions are welcome, whether it's code,
            documentation, or design improvements.
          </p>
          <Button asChild size="lg" variant="outline">
            <a
              href="https://github.com/Jon-MarkHampson/ai-meme-generator"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2"
            >
              View on GitHub
              <ExternalLink className="h-4 w-4" />
            </a>
          </Button>
        </div>
      </div>
    </div>
  )
}
