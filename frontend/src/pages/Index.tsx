import { useState, useEffect } from 'react';
import { Menu, Printer, Eye, RefreshCw, Plus } from 'lucide-react';
import { formatDate } from '@/lib/date';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { CategorySelector } from '@/components/CategorySelector';
import { Sidebar } from '@/components/Sidebar';
import { IconPicker } from '@/components/IconPicker';
import { CategoryList } from '@/components/CategoryList';
import { TemplateList } from '@/components/TemplateList';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import {
  Category,
  Template,
  Note,
  getCategories,
  getTemplates,
  getNotes,
  createNote,
  createCategory,
  createTemplate,
  updateCategory as apiUpdateCategory,
  updateTemplate as apiUpdateTemplate,
  deleteCategory as apiDeleteCategory,
  deleteTemplate as apiDeleteTemplate,
  reprintNote,
  getNotePreview,
} from '@/lib/api';
import { getLastCategory, setLastCategory, getLastTemplate, setLastTemplate } from '@/lib/storage';

type Page = 'home' | 'categories' | 'templates';
type Dialog = 'category-picker' | 'icon-picker' | 'create-category' | 'create-template' | 'view-note' | null;

const Index = () => {
  const { toast } = useToast();
  const [page, setPage] = useState<Page>('home');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeDialog, setActiveDialog] = useState<Dialog>(null);
  
  const [noteContent, setNoteContent] = useState('');
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null);
  
  const [categories, setCategories] = useState<Category[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryLabel, setNewCategoryLabel] = useState('');
  const [newCategoryIcon, setNewCategoryIcon] = useState('');
  const [newCategoryColor, setNewCategoryColor] = useState('#3B82F6');
  
  const [newTemplateName, setNewTemplateName] = useState('');
  const [newTemplateHtml, setNewTemplateHtml] = useState('');
  
  const [viewingNote, setViewingNote] = useState<Note | null>(null);
  const [viewingNoteHtml, setViewingNoteHtml] = useState<string>('');
  const [recentCategories, setRecentCategories] = useState<Category[]>([]);
  
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  // Save to localStorage whenever selections change
  useEffect(() => {
    if (selectedCategoryId !== null) {
      setLastCategory(selectedCategoryId);
    }
  }, [selectedCategoryId]);

  useEffect(() => {
    if (selectedTemplateId !== null) {
      setLastTemplate(selectedTemplateId);
    }
  }, [selectedTemplateId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [categoriesData, templatesData, notesData] = await Promise.all([
        getCategories(),
        getTemplates(),
        getNotes(1, 10),
      ]);
      
      setCategories(categoriesData);
      setTemplates(templatesData);
      setNotes(notesData.data || []);
      
      // Extract last 4 unique categories from the last 10 notes
      const notesArray = notesData.data || [];
      const uniqueCategoryIds = [...new Set(notesArray.map(note => note.category_id))];
      const recentCategoryIds = uniqueCategoryIds.slice(0, 4);
      const recent = recentCategoryIds
        .map(id => categoriesData.find(c => c.id === id))
        .filter((c): c is Category => c !== undefined);
      setRecentCategories(recent);
      
      // Load last selected category and template
      const lastCat = getLastCategory();
      const lastTpl = getLastTemplate();
      if (lastCat && categoriesData.some(c => c.id === lastCat)) {
        setSelectedCategoryId(lastCat);
      }
      if (lastTpl && templatesData.some(t => t.id === lastTpl)) {
        setSelectedTemplateId(lastTpl);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
      toast({
        title: 'Error loading data',
        description: 'Please refresh the page',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = async () => {
    if (!noteContent.trim() || !selectedCategoryId) {
      toast({
        title: 'Missing information',
        description: 'Please select a category and enter note content',
        variant: 'destructive',
      });
      return;
    }

    toast({
      title: 'Printing...',
      description: 'Sending to printer',
    });

    try {
      await createNote({
        category_id: selectedCategoryId,
        text: noteContent,
        template_id: selectedTemplateId,
        should_print: true,
        width: 384,
      });

      toast({
        title: '✓ Printed successfully!',
        description: 'Note has been saved and printed',
      });

      setNoteContent('');
      setSelectedTemplateId(null);
      loadData();
    } catch (error) {
      console.error('Failed to print note:', error);
      toast({
        title: 'Print failed',
        description: 'Failed to send note to printer',
        variant: 'destructive',
      });
    }
  };

  const handleTemplateSelect = (templateId: number) => {
    setSelectedTemplateId(templateId);
  };

  const handleCreateCategory = async () => {
    if (!newCategoryName.trim() || !newCategoryLabel.trim() || !newCategoryIcon) {
      toast({
        title: 'Missing information',
        description: 'Please enter name, label, and select an icon',
        variant: 'destructive',
      });
      return;
    }

    try {
      const newCategory = await createCategory({
        name: newCategoryName,
        label: newCategoryLabel,
        icon: newCategoryIcon,
        color: newCategoryColor,
        is_active: true,
      });

      toast({
        title: 'Success!',
        description: 'Category created',
      });
      
      setActiveDialog(null);
      setNewCategoryName('');
      setNewCategoryLabel('');
      setNewCategoryIcon('');
      setNewCategoryColor('#3B82F6');
      setSelectedCategoryId(newCategory.id);
      await loadData();
    } catch (error) {
      console.error('Failed to create category:', error);
      toast({
        title: 'Error',
        description: 'Failed to create category',
        variant: 'destructive',
      });
    }
  };
  
  const handleUpdateCategory = async () => {
    if (!editingCategory || !newCategoryName || !newCategoryLabel || !newCategoryIcon) {
      toast({
        title: 'Missing information',
        description: 'Please fill in all fields',
        variant: 'destructive',
      });
      return;
    }

    try {
      await apiUpdateCategory(editingCategory.id, {
        name: newCategoryName,
        label: newCategoryLabel,
        icon: newCategoryIcon,
        color: newCategoryColor,
        is_active: editingCategory.is_active ?? true,
      });
      
      toast({
        title: 'Success!',
        description: 'Category updated',
      });
      
      setActiveDialog(null);
      setEditingCategory(null);
      setNewCategoryName('');
      setNewCategoryLabel('');
      setNewCategoryIcon('');
      setNewCategoryColor('#3B82F6');
      await loadData();
    } catch (error) {
      console.error('Failed to update category:', error);
      toast({
        title: 'Error',
        description: 'Failed to update category',
        variant: 'destructive',
      });
    }
  };

  const handleCreateTemplate = async () => {
    if (!newTemplateName.trim()) {
      toast({
        title: 'Missing information',
        description: 'Please enter a template name',
        variant: 'destructive',
      });
      return;
    }

    try {
      await createTemplate({
        name: newTemplateName,
        template_html: newTemplateHtml,
        is_active: true,
      });

      setNewTemplateName('');
      setNewTemplateHtml('');
      setActiveDialog(null);
      loadData();
      
      toast({
        title: 'Template created',
        description: `"${newTemplateName}" has been created`,
      });
    } catch (error) {
      console.error('Failed to create template:', error);
      toast({
        title: 'Failed to create template',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteCategory = async (id: number) => {
    try {
      await apiDeleteCategory(id);
      loadData();
      toast({
        title: 'Category deleted',
      });
    } catch (error) {
      console.error('Failed to delete category:', error);
      toast({
        title: 'Failed to delete category',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteTemplate = async (id: number) => {
    try {
      await apiDeleteTemplate(id);
      loadData();
      toast({
        title: 'Template deleted',
      });
    } catch (error) {
      console.error('Failed to delete template:', error);
      toast({
        title: 'Failed to delete template',
        variant: 'destructive',
      });
    }
  };
  
  const handleUpdateTemplate = async () => {
    if (!editingTemplate || !newTemplateName || !newTemplateHtml) {
      toast({
        title: 'Missing information',
        description: 'Please fill in all fields',
        variant: 'destructive',
      });
      return;
    }

    try {
      await apiUpdateTemplate(editingTemplate.id, {
        name: newTemplateName,
        template_html: newTemplateHtml,
        is_active: editingTemplate.is_active ?? true,
      });
      
      toast({
        title: 'Success!',
        description: 'Template updated',
      });
      
      setActiveDialog(null);
      setEditingTemplate(null);
      setNewTemplateName('');
      setNewTemplateHtml('');
      await loadData();
    } catch (error) {
      console.error('Failed to update template:', error);
      toast({
        title: 'Error',
        description: 'Failed to update template',
        variant: 'destructive',
      });
    }
  };


  const handleViewNote = async (note: Note) => {
    setViewingNote(note);
    setActiveDialog('view-note');
    try {
      const html = await getNotePreview(note.id, 'html');
      setViewingNoteHtml(html);
    } catch (error) {
      console.error('Failed to fetch note preview:', error);
      setViewingNoteHtml('');
    }
  };

  const handleReprintNote = async (note: Note) => {
    try {
      await reprintNote(note.id);
      toast({
        title: 'Sent to printer',
        description: 'Note has been sent to the printer',
      });
    } catch (error) {
      console.error('Failed to reprint note:', error);
      toast({
        title: 'Failed to reprint',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b bg-card px-4 py-3 flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(true)}>
          <Menu className="h-5 w-5" />
        </Button>
        <h1 className="text-lg font-bold flex-1">Matheus and Pamella's Board Notes</h1>
      </header>

      {/* Main Content */}
      <main className="flex-1 px-3 py-4 space-y-6 max-w-2xl mx-auto w-full">
        {page === 'home' && (
          <>
            {/* Quick Input */}
            <div className="bg-card rounded-xl border p-4 space-y-5 shadow-sm">
              <CategorySelector
                selectedCategoryId={selectedCategoryId}
                onSelect={setSelectedCategoryId}
                onAddNew={() => setActiveDialog('category-picker')}
                recentCategories={recentCategories}
              />

              <div className="space-y-3">
                <label className="text-sm font-semibold text-foreground">Template</label>
                <Select
                  value={selectedTemplateId?.toString() || ''}
                  onValueChange={(value) => handleTemplateSelect(parseInt(value))}
                >
                  <SelectTrigger className="h-11">
                    <SelectValue placeholder="Choose a template" />
                  </SelectTrigger>
                  <SelectContent>
                    {templates.map((template) => (
                      <SelectItem key={template.id} value={template.id.toString()}>
                        {template.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-3">
                <label className="text-sm font-semibold text-foreground">Write your note</label>
                <Textarea
                  placeholder="Type your note here..."
                  value={noteContent}
                  onChange={(e) => setNoteContent(e.target.value)}
                  className="min-h-[160px] receipt-font resize-none text-base border-2 focus-visible:border-accent bg-input rounded-2xl"
                />
              </div>

              <Button
                onClick={handlePrint}
                className="w-full h-12 text-base font-semibold shadow-lg hover:shadow-xl transition-all"
                disabled={!noteContent.trim() || !selectedCategoryId}
              >
                <Printer className="mr-2 h-5 w-5" />
                Print note
              </Button>
            </div>

            {/* Recent Notes */}
            <div className="space-y-4">
              <h2 className="font-serif text-lg font-bold text-foreground px-1">Recent Notes</h2>
              <div className="space-y-3">
                {notes.length === 0 ? (
                  <div className="bg-card rounded-2xl p-8 text-center border border-border">
                    <p className="text-muted-foreground">No notes yet</p>
                  </div>
                ) : (
                  notes.map((note) => {
                    const category = categories.find(c => c.id === note.category_id);
                    return (
                      <div
                        key={note.id}
                        className="bg-card rounded-2xl p-4 shadow-sm border border-border hover:shadow-md transition-all"
                      >
                        <div className="flex items-start gap-3">
                          {category && (
                            <div
                              className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center"
                              style={{ backgroundColor: category.color }}
                            >
                              <span
                                dangerouslySetInnerHTML={{ __html: category.icon }}
                                className="w-5 h-5 flex items-center justify-center [&>svg]:w-full [&>svg]:h-full text-white"
                              />
                            </div>
                          )}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-secondary text-secondary-foreground">
                                {category?.label}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {formatDate(note.created_at || note.date, 'relative')}
                              </span>
                            </div>
                            <p className="text-sm text-foreground line-clamp-2 receipt-font">
                              {note.text}
                            </p>
                          </div>
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 rounded-full"
                              onClick={() => handleViewNote(note)}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 rounded-full"
                              onClick={() => handleReprintNote(note)}
                            >
                              <RefreshCw className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </>
        )}

        {page === 'categories' && (
          <div className="h-[calc(100vh-8rem)]">
            <CategoryList
              categories={categories}
              onSelect={(category) => {
                setSelectedCategoryId(category.id);
                setPage('home');
              }}
              onCreate={() => setActiveDialog('create-category')}
              onDelete={handleDeleteCategory}
              onEdit={(category) => {
                setEditingCategory(category);
                setNewCategoryName(category.name);
                setNewCategoryLabel(category.label);
                setNewCategoryIcon(category.icon);
                setNewCategoryColor(category.color);
                setActiveDialog('create-category');
              }}
            />
          </div>
        )}

        {page === 'templates' && (
          <div className="h-[calc(100vh-8rem)]">
            <TemplateList
              templates={templates}
              onSelect={(template) => {
                setSelectedTemplateId(template.id);
                setPage('home');
              }}
              onCreate={() => setActiveDialog('create-template')}
              onDelete={handleDeleteTemplate}
              onEdit={(template) => {
                setEditingTemplate(template);
                setNewTemplateName(template.name);
                setNewTemplateHtml(template.template_html);
                setActiveDialog('create-template');
              }}
            />
          </div>
        )}
      </main>

      {/* Sidebar */}
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNavigate={(p) => setPage(p)}
      />

      {/* Category Picker Dialog */}
      <Dialog open={activeDialog === 'category-picker'} onOpenChange={() => setActiveDialog(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <span>Select Category</span>
              <span className="text-sm font-normal text-muted-foreground">
                {categories.length} {categories.length === 1 ? 'category' : 'categories'}
              </span>
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <Input 
              placeholder="Search categories..." 
              className="w-full"
              onChange={(e) => {
                // Filter categories - for now just visual, you can add state if needed
                const value = e.target.value.toLowerCase();
                const items = document.querySelectorAll('[data-category-name]');
                items.forEach((item) => {
                  const name = item.getAttribute('data-category-name') || '';
                  (item as HTMLElement).style.display = name.includes(value) ? '' : 'none';
                });
              }}
            />
            <div className="space-y-2 max-h-[50vh] overflow-y-auto pr-1">
              {categories.map((category) => {
                const isSelected = selectedCategoryId === category.id;
                return (
                  <button
                    key={category.id}
                    data-category-name={category.label.toLowerCase()}
                    onClick={() => {
                      setSelectedCategoryId(category.id);
                      setActiveDialog(null);
                      toast({ title: 'Category selected', description: category.label });
                    }}
                    className={`w-full flex items-center gap-3 p-3 rounded-xl border-2 transition-all ${
                      isSelected 
                        ? 'border-accent bg-accent/10 shadow-sm' 
                        : 'border-border hover:bg-accent/5 hover:border-accent/50'
                    }`}
                  >
                    <span 
                      dangerouslySetInnerHTML={{ __html: category.icon }}
                      className="w-7 h-7 flex items-center justify-center [&>svg]:w-full [&>svg]:h-full"
                      style={{ color: category.color }}
                    />
                    <span className="font-medium flex-1 text-left">{category.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
          <div className="sticky bottom-0 pt-3 bg-card border-t mt-2">
            <Button
              variant="outline"
              className="w-full border-2 border-dashed hover:border-accent hover:bg-accent/5"
              onClick={() => setActiveDialog('create-category')}
            >
              <Plus className="mr-2 h-4 w-4" />
              Create New Category
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Create Category Dialog */}
      <Dialog open={activeDialog === 'create-category'} onOpenChange={(open) => {
        if (!open) {
          setActiveDialog(null);
          setEditingCategory(null);
          setNewCategoryName('');
          setNewCategoryLabel('');
          setNewCategoryIcon('');
          setNewCategoryColor('#3B82F6');
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingCategory ? 'Edit Category' : 'Create Category'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="category-name">Name (identifier)</Label>
              <Input
                id="category-name"
                value={newCategoryName}
                onChange={(e) => setNewCategoryName(e.target.value)}
                placeholder="e.g., work, home"
              />
            </div>
            <div>
              <Label htmlFor="category-label">Label (display name)</Label>
              <Input
                id="category-label"
                value={newCategoryLabel}
                onChange={(e) => setNewCategoryLabel(e.target.value)}
                placeholder="e.g., Work, Home"
              />
            </div>
            <div>
              <Label htmlFor="category-color">Color</Label>
              <div className="flex gap-2">
                <Input
                  id="category-color"
                  type="color"
                  value={newCategoryColor}
                  onChange={(e) => setNewCategoryColor(e.target.value)}
                  className="w-20 h-10"
                />
                <Input
                  value={newCategoryColor}
                  onChange={(e) => setNewCategoryColor(e.target.value)}
                  placeholder="#3B82F6"
                  className="flex-1"
                />
              </div>
            </div>
            <div>
              <Label>Icon</Label>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => setActiveDialog('icon-picker')}
              >
                {newCategoryIcon ? (
                  <span 
                    dangerouslySetInnerHTML={{ __html: newCategoryIcon }}
                    className="w-5 h-5 mr-2 flex items-center justify-center [&>svg]:w-full [&>svg]:h-full"
                    style={{ color: newCategoryColor }}
                  />
                ) : (
                  'Select an icon'
                )}
              </Button>
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                onClick={() => {
                  setActiveDialog(null);
                  setEditingCategory(null);
                  setNewCategoryName('');
                  setNewCategoryLabel('');
                  setNewCategoryIcon('');
                  setNewCategoryColor('#3B82F6');
                }} 
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                onClick={editingCategory ? handleUpdateCategory : handleCreateCategory}
                className="flex-1"
              >
                {editingCategory ? 'Update' : 'Create'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Icon Picker */}
      {activeDialog === 'icon-picker' && (
        <IconPicker
          onSelect={(svgString) => {
            setNewCategoryIcon(svgString);
            setActiveDialog('create-category');
          }}
          onClose={() => setActiveDialog('create-category')}
        />
      )}

      {/* Create Template Dialog */}
      <Dialog open={activeDialog === 'create-template'} onOpenChange={(open) => {
        if (!open) {
          setActiveDialog(null);
          setEditingTemplate(null);
          setNewTemplateName('');
          setNewTemplateHtml('');
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingTemplate ? 'Edit Template' : 'Create Template'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="template-name">Name</Label>
              <Input
                id="template-name"
                value={newTemplateName}
                onChange={(e) => setNewTemplateName(e.target.value)}
                placeholder="Template name"
              />
            </div>
            <div>
              <Label htmlFor="template-content">HTML Content</Label>
              <Textarea
                id="template-content"
                value={newTemplateHtml}
                onChange={(e) => setNewTemplateHtml(e.target.value)}
                placeholder="HTML template content (optional)"
                className="min-h-[120px] receipt-font font-mono text-xs"
              />
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                onClick={() => {
                  setActiveDialog(null);
                  setEditingTemplate(null);
                  setNewTemplateName('');
                  setNewTemplateHtml('');
                }} 
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                onClick={editingTemplate ? handleUpdateTemplate : handleCreateTemplate}
                className="flex-1"
              >
                {editingTemplate ? 'Update' : 'Create'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* View Note Dialog */}
      <Dialog open={activeDialog === 'view-note'} onOpenChange={() => setActiveDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>View Note</DialogTitle>
          </DialogHeader>
          {viewingNote && (
            <div className="space-y-4">
              <div className="bg-receipt-bg border-receipt-border border rounded-lg p-4">
                <p className="receipt-font text-receipt-text whitespace-pre-wrap break-all">
                  {viewingNote.text}
                </p>
              </div>
              <div className="text-sm text-muted-foreground">
                {new Date(viewingNote.created_at).toLocaleString()}
              </div>
              <Button
                onClick={() => {
                  handleReprintNote(viewingNote);
                  setActiveDialog(null);
                }}
                className="w-full"
              >
                <Printer className="mr-2 h-4 w-4" />
                Print Again
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Index;
