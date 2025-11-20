import { Sheet, SheetContent } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { FolderOpen, FileText, Home, Settings } from 'lucide-react';

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  onNavigate: (page: 'home' | 'categories' | 'templates') => void;
}

export const Sidebar = ({ open, onClose, onNavigate }: SidebarProps) => {
  const handleNavigation = (page: 'home' | 'categories' | 'templates') => {
    onNavigate(page);
    onClose();
  };

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent side="left" className="w-72 p-0">
        {/* Header */}
        <div className="p-6 border-b border-border bg-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <FileText className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h2 className="font-serif font-bold text-lg text-foreground">Matheus and Pamella's Board Notes</h2>
              <p className="text-xs text-muted-foreground">Quick board notes</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-1 p-4">
          <Button
            variant="ghost"
            className="justify-start h-12 px-4 rounded-full hover:bg-accent/50"
            onClick={() => handleNavigation('home')}
          >
            <Home className="mr-3 h-5 w-5" />
            <span className="font-medium">Home</span>
          </Button>
          <Button
            variant="ghost"
            className="justify-start h-12 px-4 rounded-full hover:bg-accent/50"
            onClick={() => handleNavigation('categories')}
          >
            <FolderOpen className="mr-3 h-5 w-5" />
            <span className="font-medium">Categories</span>
          </Button>
          <Button
            variant="ghost"
            className="justify-start h-12 px-4 rounded-full hover:bg-accent/50"
            onClick={() => handleNavigation('templates')}
          >
            <FileText className="mr-3 h-5 w-5" />
            <span className="font-medium">Templates</span>
          </Button>
          <Button
            variant="ghost"
            className="justify-start h-12 px-4 rounded-full hover:bg-accent/50"
          >
            <Settings className="mr-3 h-5 w-5" />
            <span className="font-medium">Printer settings</span>
          </Button>
        </nav>
      </SheetContent>
    </Sheet>
  );
};
