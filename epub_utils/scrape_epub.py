import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup


FILE_DIR = "/tmp"


class EPubScraper:
    def extract_text_from_epub(self, epub_file_path: str) -> str:
        """
        Extracts the text content from an EPUB file.
        EPUBs are typically downloaded from annas-archive.li
        """
        book = epub.read_epub(epub_file_path)
        title = book.get_metadata("DC", "title")[0][0]
        text = ""
        for i, item in enumerate(book.get_items_of_type(ebooklib.ITEM_DOCUMENT)):
            text += BeautifulSoup(item.get_content(), "html.parser").get_text()
        scraped_epub_text_filepath = f"{FILE_DIR}/{title}.txt"
        with open(scraped_epub_text_filepath, "w") as f:
            f.write(text)
        return scraped_epub_text_filepath
