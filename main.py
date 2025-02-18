import sqlite3
import os
from pathlib import Path
import json
import re
import argparse

class ZoteroObsidianSync:
    def __init__(self, zotero_db_path, obsidian_vault_path):
        """
        Initialize the sync tool with paths to Zotero database and Obsidian vault.

        Args:
            zotero_db_path (str): Path to zotero.sqlite database
            obsidian_vault_path (str): Path to Obsidian vault
        """
        self.zotero_db_path = zotero_db_path
        self.obsidian_vault_path = Path(obsidian_vault_path)
        self.papers_folder = self.obsidian_vault_path / "Academic Papers"
        self.papers_folder.mkdir(exist_ok=True)

    def connect_to_zotero(self):
        """Create a connection to the Zotero SQLite database."""
        return sqlite3.connect(self.zotero_db_path)

    def get_zotero_items(self):
        """
        Retrieve all academic papers from Zotero database with their metadata.

        Returns:
            list: List of dictionaries containing paper metadata
        """
        conn = self.connect_to_zotero()
        cursor = conn.cursor()

        query = """
            SELECT
                items.itemID,
                items.key,
                itemTypes.typeName,
                fields.fieldName,
                itemDataValues.value
            FROM items
            JOIN itemTypes ON items.itemTypeID = itemTypes.itemTypeID
            JOIN itemData ON items.itemID = itemData.itemID
            JOIN itemDataValues ON itemData.valueID = itemDataValues.valueID
            JOIN fields ON itemData.fieldID = fields.fieldID
            WHERE itemTypes.typeName IN ('journalArticle', 'conferencePaper', 'report', 'thesis', 'book', 'bookSection')
            AND items.itemID NOT IN (
                SELECT itemID FROM itemAttachments
            )
            ORDER BY items.itemID, fields.fieldName;
        """

        cursor.execute(query)
        results = cursor.fetchall()
        print("len results", len(results))
        print("first result", results[0])

        # Process results into a more usable format
        papers = {}
        for item_id, key, type_name, field_name, value in results:
            if item_id not in papers:
                papers[item_id] = {
                    'key': key,
                    'tags': self.get_item_tags(cursor, item_id)
                }
            papers[item_id][field_name] = value

        conn.close()
        print("len values", len(papers.values()))
        out = list(papers.values())
        print("first out", out[0])
        print("first title:", out[0].get('title'))
        return out

    def get_item_tags(self, cursor, item_id):
        """
        Get all tags for a specific item.

        Args:
            cursor: SQLite cursor
            item_id (int): Zotero item ID

        Returns:
            list: List of tags
        """
        query = """
        SELECT tags.name
        FROM itemTags
        JOIN tags ON itemTags.tagID = tags.tagID
        WHERE itemTags.itemID = ?
        """
        cursor.execute(query, (item_id,))
        return [tag[0] for tag in cursor.fetchall()]

    def create_markdown_file(self, paper):
        """
        Create a markdown file for a paper with metadata in YAML frontmatter.

        Args:
            paper (dict): Paper metadata
        """
        title = paper.get('title', 'Untitled Paper')
        print("creating markdown file for", title)
        safe_title = re.sub(r'[<>:"/\\|?*]', '-', title)  # Remove invalid filename characters

        # Create YAML frontmatter
        frontmatter = [
            '---',
            f'title: "{title}"',
            'type: academic-paper',
            f'authors: "{paper.get("author", "Unknown")}"',
            f'year: {paper.get("year", "Unknown")}',
            f'zotero-key: {paper.get("key", "")}',
        ]

        # Add tags
        if paper.get('tags'):
            frontmatter.append(f'tags: {json.dumps(paper["tags"])}')

        frontmatter.append('---\n')

        # Add metadata table for Dataview
        content = [
            '## Metadata',
            '```dataview',
            'TABLE',
            '    authors AS Authors,',
            '    year AS Year,',
            '    tags AS Tags',
            'WHERE file = this.file',
            '```\n',
            '## Notes',
            'Add your notes about the paper here.\n',
            '## Summary',
            'Add a summary of the paper here.\n',
            '## Key Points',
            '- Point 1',
            '- Point 2',
            '- Point 3\n',
            '## References',
            f'- Zotero Key: {paper.get("key", "")}',
            f'- DOI: {paper.get("DOI", "")}'
        ]

        # Write to file
        file_path = self.papers_folder / f"{safe_title}.md"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(frontmatter + content))

    def sync(self):
        """
        Synchronize Zotero library with Obsidian vault.
        """
        papers = self.get_zotero_items()
        for paper in papers:
            self.create_markdown_file(paper)
        print(f"Synchronized {len(papers)} papers to Obsidian vault")

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync Zotero library with Obsidian vault.")
    parser.add_argument('--zotero-db', type=str, default="~/Zotero/zotero.sqlite", help='Path to Zotero SQLite database')
    parser.add_argument('--obsidian-vault', type=str, default="~/Documents/ObsidianVault", help='Path to Obsidian vault')

    args = parser.parse_args()

    ZOTERO_DB = args.zotero_db
    OBSIDIAN_VAULT = args.obsidian_vault

    syncer = ZoteroObsidianSync(
        os.path.expanduser(ZOTERO_DB),
        os.path.expanduser(OBSIDIAN_VAULT)
    )
    syncer.sync()
