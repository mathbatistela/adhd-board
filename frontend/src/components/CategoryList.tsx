import { useState } from 'react';
import { Search, Plus, Trash2, Pencil } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Category } from '@/lib/api';

interface CategoryListProps {
  categories: Category[];
  onSelect: (category: Category) => void;
  onCreate: () => void;
  onDelete: (id: number) => void;
  onEdit: (category: Category) => void;
}

export const CategoryList = ({ categories, onSelect, onCreate, onDelete, onEdit }: CategoryListProps) => {
  const [search, setSearch] = useState('');

  const filteredCategories = categories.filter(cat =>
    cat.label.toLowerCase().includes(search.toLowerCase()) ||
    cat.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full">
      <div className="flex gap-2 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search categories..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button onClick={onCreate}>
          <Plus className="h-4 w-4 mr-2" />
          New
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-2">
          {filteredCategories.map((category) => (
            <div
              key={category.id}
              className="flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-accent/5 cursor-pointer group"
              onClick={() => onSelect(category)}
            >
              <span 
                dangerouslySetInnerHTML={{ __html: category.icon }}
                className="w-8 h-8 flex items-center justify-center [&>svg]:w-full [&>svg]:h-full flex-shrink-0"
                style={{ color: category.color }}
              />
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{category.name}</p>
                <p className="text-sm text-muted-foreground truncate">{category.label}</p>
              </div>
              <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation();
                    onEdit(category);
                  }}
                  className="hover:bg-accent/10"
                >
                  <Pencil className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(category.id);
                  }}
                  className="hover:bg-destructive/10 hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
};
