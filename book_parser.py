import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import requests
from bs4 import BeautifulSoup
import csv
import json
import os
from datetime import datetime
import threading

class BookParserApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Book Parser Pro v1.0")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Переменные
        self.books_data = []
        self.is_parsing = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Создание пользовательского интерфейса"""
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка расширения строк и колонок
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_frame, 
                               text="📚 Book Parser Pro", 
                               font=("Arial", 16, "bold"),
                               foreground="#2E86AB")
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Фрейм настроек
        settings_frame = ttk.LabelFrame(main_frame, text="Настройки парсинга", padding="10")
        settings_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)
        
        # URL для парсинга
        ttk.Label(settings_frame, text="URL сайта:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.url_var = tk.StringVar(value="http://books.toscrape.com/")
        url_entry = ttk.Entry(settings_frame, textvariable=self.url_var, width=50)
        url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Количество страниц
        ttk.Label(settings_frame, text="Страниц:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.pages_var = tk.StringVar(value="1")
        pages_spin = ttk.Spinbox(settings_frame, from_=1, to=50, textvariable=self.pages_var, width=5)
        pages_spin.grid(row=0, column=3, sticky=tk.W)
        
        # Фрейм кнопок
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        # Кнопки управления
        self.parse_btn = ttk.Button(buttons_frame, 
                                   text="🚀 Начать парсинг", 
                                   command=self.start_parsing,
                                   style="Accent.TButton")
        self.parse_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.export_csv_btn = ttk.Button(buttons_frame, 
                                        text="💾 Экспорт в CSV", 
                                        command=self.export_csv,
                                        state="disabled")
        self.export_csv_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.export_json_btn = ttk.Button(buttons_frame, 
                                         text="📊 Экспорт в JSON", 
                                         command=self.export_json,
                                         state="disabled")
        self.export_json_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Прогресс-бар
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Текстовое поле для логов
        log_frame = ttk.LabelFrame(main_frame, text="Лог выполнения", padding="5")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def log_message(self, message):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def start_parsing(self):
        """Запуск парсинга в отдельном потоке"""
        if self.is_parsing:
            return
            
        self.is_parsing = True
        self.parse_btn.config(state="disabled")
        self.export_csv_btn.config(state="disabled")
        self.export_json_btn.config(state="disabled")
        self.progress.start()
        self.books_data = []
        self.log_text.delete(1.0, tk.END)
        
        # Запуск в отдельном потоке чтобы не блокировать GUI
        thread = threading.Thread(target=self.parse_books)
        thread.daemon = True
        thread.start()
        
    def parse_books(self):
        """Основная функция парсинга"""
        try:
            self.log_message("🔄 Начинаем парсинг книг...")
            self.status_var.set("Парсинг запущен...")
            
            base_url = self.url_var.get()
            pages_to_parse = int(self.pages_var.get())
            
            for page in range(1, pages_to_parse + 1):
                if page == 1:
                    url = base_url
                else:
                    url = f"{base_url}catalogue/page-{page}.html"
                
                self.log_message(f"📄 Обрабатываем страницу {page}: {url}")
                
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    books = soup.find_all('article', class_='product_pod')
                    
                    self.log_message(f"📚 Найдено книг на странице: {len(books)}")
                    
                    for book in books:
                        book_data = self.parse_single_book(book, base_url)
                        if book_data:
                            self.books_data.append(book_data)
                            
                except Exception as e:
                    self.log_message(f"❌ Ошибка на странице {page}: {e}")
                    continue
            
            self.log_message(f"✅ Парсинг завершен! Обработано книг: {len(self.books_data)}")
            self.status_var.set(f"Готово! Обработано книг: {len(self.books_data)}")
            
            # Активируем кнопки экспорта
            self.export_csv_btn.config(state="normal")
            self.export_json_btn.config(state="normal")
            
        except Exception as e:
            self.log_message(f"❌ Критическая ошибка: {e}")
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")
        finally:
            self.is_parsing = False
            self.parse_btn.config(state="normal")
            self.progress.stop()
            
    def parse_single_book(self, book, base_url):
        """Парсинг одной книги"""
        try:
            # Название книги
            title = book.h3.a['title']
            
            # Цена
            price = book.find('p', class_='price_color').text
            
            # Наличие
            availability = book.find('p', class_='instock').text.strip()
            
            # Рейтинг
            rating_classes = book.p['class']
            rating = [cls for cls in rating_classes if 'star' in cls][0] if rating_classes else 'No rating'
            rating = rating.replace('star-rating', '').strip()
            
            # Ссылка на книгу
            book_link = book.h3.a['href']
            if book_link.startswith('../../../'):
                book_link = book_link.replace('../../../', '')
                full_link = f"{base_url}{book_link}"
            else:
                full_link = f"{base_url}catalogue/{book_link}"
            
            book_data = {
                'title': title,
                'price': price,
                'availability': availability,
                'rating': rating,
                'link': full_link
            }
            
            self.log_message(f"   📖 Добавлена: {title} - {price}")
            
            return book_data
            
        except Exception as e:
            self.log_message(f"   ⚠️ Ошибка парсинга книги: {e}")
            return None
            
    def export_csv(self):
        """Экспорт данных в CSV"""
        if not self.books_data:
            messagebox.showwarning("Предупреждение", "Нет данных для экспорта!")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Сохранить как CSV"
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=self.books_data[0].keys())
                    writer.writeheader()
                    writer.writerows(self.books_data)
                    
                self.log_message(f"💾 Данные экспортированы в: {filename}")
                messagebox.showinfo("Успех", f"Данные успешно экспортированы в:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при экспорте: {e}")
                
    def export_json(self):
        """Экспорт данных в JSON"""
        if not self.books_data:
            messagebox.showwarning("Предупреждение", "Нет данных для экспорта!")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Сохранить как JSON"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as file:
                    json.dump(self.books_data, file, ensure_ascii=False, indent=2)
                    
                self.log_message(f"📊 Данные экспортированы в: {filename}")
                messagebox.showinfo("Успех", f"Данные успешно экспортированы в:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при экспорте: {e}")
    
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()

if __name__ == "__main__":
    # Создаем стиль для акцентной кнопки
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    app = BookParserApp()
    app.run()