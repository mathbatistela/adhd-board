import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Category } from '@/lib/api';

interface CategorySelectorProps {
  selectedCategoryId: number | null;
  onSelect: (categoryId: number) => void;
  onAddNew: () => void;
  recentCategories?: Category[];
}

export const CategorySelector = ({ selectedCategoryId, onSelect, onAddNew, recentCategories = [] }: CategorySelectorProps) => {
  return (
    <div className="space-y-3">
      <label className="text-sm font-semibold text-foreground">Category</label>
      <div className="flex gap-3 overflow-x-auto pb-2 px-2 scrollbar-hide">
        {recentCategories.slice(0, 4).map((category) => {
          const isSelected = selectedCategoryId === category.id;
          return (
          <button
            key={category.id}
            onClick={() => onSelect(category.id)}
            className={`flex-shrink-0 flex items-center justify-center rounded-full transition-all w-[60px] h-[60px] shadow-sm aspect-square ${
              isSelected
                ? 'shadow-md'
                : 'bg-card border-2 border-border hover:border-accent/50 hover:shadow-md'
            }`}
            style={{ backgroundColor: isSelected ? category.color : undefined }}
          >
            <span 
              dangerouslySetInnerHTML={{ __html: category.icon }}
              className="w-6 h-6 flex items-center justify-center [&>svg]:w-full [&>svg]:h-full [&>svg]:fill-current"
              style={{ color: isSelected ? 'white' : category.color }}
            />
          </button>
          );
        })}
        
        <button
          onClick={onAddNew}
          className="flex-shrink-0 flex items-center justify-center rounded-full border-2 border-dashed border-border hover:border-accent/50 hover:bg-accent/5 transition-all w-[60px] h-[60px] shadow-sm hover:shadow-md bg-card aspect-square"
        >
          <Plus className="h-6 w-6 text-muted-foreground" />
        </button>
      </div>
    </div>
  );
};
