import { useState } from "react";
import { HiMenu, HiX } from "react-icons/hi";
import { FaLinkedin, FaTwitter, FaDiscord, FaGithub } from 'react-icons/fa';
import Link from "next/link";
import { useRouter } from "next/router";

const Header = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const router = useRouter();
  
  const isActive = (path: string) => {
    return router.pathname === path;
  };

  return (
    <header className="fixed w-full z-10">
      <div className="px-6 py-5 flex justify-between items-center bg-gray-100 shadow-md">
        <div className="flex items-center">
          <Link href="/" className="flex items-center text-xl font-bold text-gray-900 mr-12">
            <img 
              src="/pathonai_org.png" 
              alt="PathOnAI Logo" 
              className="h-8 w-auto mr-2" 
            />
            PathOnAI
          </Link>
          <nav className="hidden md:flex space-x-8">
            <Link 
              href="https://www.pathonai.org/projects/litewebagent" 
              className={`text-sm font-medium ${isActive('/') 
                ? 'text-blue-600' 
                : 'text-gray-700 hover:text-blue-600'}`}
            >
              LiteWebAgent Project Page
            </Link>
            <Link 
              href="https://www.pathonai.org/projects/visualtreesearch" 
              className={`text-sm font-medium ${isActive('/projects') 
                ? 'text-blue-600' 
                : 'text-gray-700 hover:text-blue-600'}`}
            >
              Visual Tree Search Project Page
            </Link>
          </nav>
        </div>
        <div className="flex items-center">
          {/* Social Media Links */}
          <div className="hidden md:flex items-center space-x-5 mr-6">
            <a
              href="https://github.com/PathOnAI"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-700 hover:text-blue-600"
              aria-label="GitHub"
            >
              <FaGithub className="h-6 w-6" />
            </a>
            <a
              href="https://www.linkedin.com/company/pathonai/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-700 hover:text-blue-600"
              aria-label="LinkedIn"
            >
              <FaLinkedin className="h-6 w-6" />
            </a>
            <a
              href="https://x.com/PathOnAI"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-700 hover:text-blue-600"
              aria-label="Twitter"
            >
              <FaTwitter className="h-6 w-6" />
            </a>
            <a
              href="https://discord.com/invite/UTxjyNwTeP"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-700 hover:text-blue-600"
              aria-label="Discord"
            >
              <FaDiscord className="h-6 w-6" />
            </a>
          </div>
          
          <div className="md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="text-gray-700"
            >
              {mobileMenuOpen ? (
                <HiX className="h-6 w-6" />
              ) : (
                <HiMenu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </div>

    </header>
  );
};

export default Header; 