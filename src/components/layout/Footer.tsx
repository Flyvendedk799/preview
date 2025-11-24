export default function Footer() {
  return (
    <footer className="border-t border-gray-200 mt-12 py-6">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          <div className="text-sm text-gray-600">
            © {new Date().getFullYear()} Preview SaaS. All rights reserved.
          </div>
          <div className="flex space-x-6 text-sm">
            <a href="/privacy" className="text-gray-600 hover:text-primary transition-colors">
              Privacy Policy
            </a>
            <a href="/terms" className="text-gray-600 hover:text-primary transition-colors">
              Terms of Service
            </a>
            <a href="/app/account" className="text-gray-600 hover:text-primary transition-colors">
              Data & Privacy
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}

