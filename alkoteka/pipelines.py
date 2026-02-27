import json
import os


class JsonWriterPipeline:
    """Pipeline to write items to JSON file"""

    def __init__(self):
        self.file = None
        self.items = []

    def open_spider(self, spider):
        self.items = []

    def process_item(self, item, spider):
        self.items.append(dict(item))
        return item

    def close_spider(self, spider):
        # Write to file
        output_file = 'result.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)
        
        spider.logger.info(f"Wrote {len(self.items)} items to {output_file}")
