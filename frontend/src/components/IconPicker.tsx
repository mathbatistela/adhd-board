import { useState, useEffect } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

interface IconPickerProps {
  onSelect: (iconSvg: string, iconSet: string) => void;
  onClose: () => void;
}

interface IconifyIcon {
  name: string;
  prefix: string;
}

export const IconPicker = ({ onSelect, onClose }: IconPickerProps) => {
  const [search, setSearch] = useState('');
  const [icons, setIcons] = useState<IconifyIcon[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIcon, setSelectedIcon] = useState<IconifyIcon | null>(null);

  useEffect(() => {
    if (search.length > 1) {
      const timer = setTimeout(() => {
        searchIcons(search);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [search]);

  const searchIcons = async (query: string) => {
    setLoading(true);
    try {
      const response = await fetch(
        `https://api.iconify.design/search?query=${encodeURIComponent(query)}&limit=50`
      );
      const data = await response.json();
      
      if (data.icons) {
        const iconList: IconifyIcon[] = data.icons.map((iconName: string) => {
          const [prefix, name] = iconName.split(':');
          return { prefix, name: iconName };
        });
        setIcons(iconList);
      }
    } catch (error) {
      console.error('Failed to search icons:', error);
    }
    setLoading(false);
  };

  const handleSelect = async () => {
    if (selectedIcon) {
      try {
        const response = await fetch(`https://api.iconify.design/${selectedIcon.name}.svg`);
        if (!response.ok) throw new Error('Failed to fetch icon');
        const svgString = await response.text();
        onSelect(svgString, selectedIcon.prefix);
        onClose();
      } catch (error) {
        console.error('Error fetching icon:', error);
      }
    }
  };

  return (
    <div className="fixed inset-0 bg-background/95 z-50 p-4 flex flex-col">
      <div className="flex items-center gap-2 mb-4">
        <Button variant="ghost" size="sm" onClick={onClose}>
          Cancel
        </Button>
        <h2 className="text-lg font-semibold flex-1">Select Icon</h2>
        <Button 
          size="sm" 
          onClick={handleSelect}
          disabled={!selectedIcon}
        >
          Select
        </Button>
      </div>

      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search icons..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
          autoFocus
        />
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {!loading && icons.length > 0 && (
        <ScrollArea className="flex-1">
          <div className="grid grid-cols-6 gap-2">
            {icons.map((icon) => (
              <button
                key={icon.name}
                onClick={() => setSelectedIcon(icon)}
                className={`aspect-square p-3 rounded-lg border-2 transition-colors hover:border-accent ${
                  selectedIcon?.name === icon.name
                    ? 'border-accent bg-accent/10'
                    : 'border-border'
                }`}
              >
                <img
                  src={`https://api.iconify.design/${icon.name}.svg`}
                  alt={icon.name}
                  className="w-full h-full"
                />
              </button>
            ))}
          </div>
        </ScrollArea>
      )}

      {!loading && search.length > 1 && icons.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          No icons found
        </div>
      )}

      {!loading && search.length <= 1 && (
        <div className="text-center py-8 text-muted-foreground">
          Type to search for icons
        </div>
      )}
    </div>
  );
};
