import { useState } from 'react';
import { Search, Plus, Trash2, Pencil } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Template } from '@/lib/api';

interface TemplateListProps {
  templates: Template[];
  onSelect: (template: Template) => void;
  onCreate: () => void;
  onDelete: (id: number) => void;
  onEdit: (template: Template) => void;
}

export const TemplateList = ({ templates, onSelect, onCreate, onDelete, onEdit }: TemplateListProps) => {
  const [search, setSearch] = useState('');

  const filteredTemplates = templates.filter(tpl =>
    tpl.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full">
      <div className="flex gap-2 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search templates..."
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
          {filteredTemplates.map((template) => (
            <div
              key={template.id}
              className="flex items-start gap-3 p-3 rounded-lg border bg-card hover:bg-accent/5 cursor-pointer group"
              onClick={() => onSelect(template)}
            >
              <div className="flex-1 min-w-0">
                <p className="font-medium mb-2">{template.name}</p>
                <div 
                  className="text-xs text-muted-foreground line-clamp-2"
                  dangerouslySetInnerHTML={{ __html: template.template_html || '(Empty template)' }}
                />
              </div>
              <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation();
                    onEdit(template);
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
                    onDelete(template.id);
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
