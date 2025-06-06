import Link from "next/link";
import { useRouter } from "next/router";
import { Home, LineChart, FileText, LogIn} from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Sidebar() {
  const router = useRouter();
  
  // Helper to add custom active styles
  const activeClass =
    "bg-blue-50 border-l-4 border-blue-600 text-blue-700 font-semibold shadow-sm";

  return (
    <div className="w-64 h-full border-r border-foreground/10 bg-background">
      <div className="p-4 border-b border-foreground/10">
        <h1 className="text-xl font-bold">LiteWebAgent</h1>
      </div>
      
      <nav className="p-2">
        <div className="space-y-1">
          <Button
            variant={router.pathname === "/" ? "secondary" : "ghost"}
            className={`w-full justify-start ${
              router.pathname === "/" ? activeClass : ""
            }`}
            asChild
          >
            <Link href="/">
              <Home className="mr-2 h-4 w-4" />
              Home
            </Link>
          </Button>

          <Button
            variant={router.pathname === "/playground" ? "secondary" : "ghost"}
            className={`w-full justify-start ${
              router.pathname === "/playground" ? activeClass : ""
            }`}
            asChild
          >
            <Link href="/playground">
              <LineChart className="mr-2 h-4 w-4" />
              Playground
            </Link>
          </Button>
          
          <Button
            variant={router.pathname === "/login" ? "secondary" : "ghost"}
            className={`w-full justify-start ${
              router.pathname === "/login" ? activeClass : ""
            }`}
            asChild
          >
            <Link href="/login">
              <LogIn className="mr-2 h-4 w-4" />
              Login
            </Link>
          </Button>
        </div>
      </nav>
    </div>
  );
} 