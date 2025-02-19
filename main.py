import sqlite3
import os
from pathlib import Path
import json
import re
import argparse
from typing import TypedDict, List, Dict, Optional


class Paper(TypedDict, total=False):
    """
    TypedDict representing a paper from Zotero.
    total=False means all fields are optional except those in the required set.
    """

    # Required fields
    key: str
    type: str
    tags: List[str]
    authors: List[str]
    # Optional fields
    title: str
    date: str
    abstractNote: str
    DOI: str
    accessDate: str
    series: str
    conferenceName: str
    publicationTitle: str


class ZoteroObsidianSync:
    def __init__(
        self,
        zotero_db_path: str,
        obsidian_vault_path: str,
        papers_folder: str = "zotero",
    ):
        """
        Initialize the sync tool with paths to Zotero database and Obsidian vault.

        Args:
            zotero_db_path: Path to zotero.sqlite database
            obsidian_vault_path: Path to Obsidian vault
            papers_folder: Name of folder to store paper notes
        """
        self.zotero_db_path = Path(zotero_db_path)
        self.obsidian_vault_path = Path(obsidian_vault_path)
        self.papers_folder = self.obsidian_vault_path / papers_folder
        self.papers_folder.mkdir(exist_ok=True)

    def connect_to_zotero(self) -> sqlite3.Connection:
        """Create a connection to the Zotero SQLite database."""
        if not self.zotero_db_path.exists():
            raise FileNotFoundError(
                f"Zotero database not found at {self.zotero_db_path}"
            )
        return sqlite3.connect(str(self.zotero_db_path))

    def get_item_tags(self, cursor: sqlite3.Cursor, item_id: int) -> List[str]:
        """Get all tags for a specific item."""
        query = """
        SELECT tags.name
        FROM itemTags
        JOIN tags ON itemTags.tagID = tags.tagID
        WHERE itemTags.itemID = ?
        """
        cursor.execute(query, (item_id,))
        return [tag[0] for tag in cursor.fetchall()]

    def get_item_authors(self, cursor: sqlite3.Cursor, item_id: int) -> List[str]:
        """Get ordered list of authors for a specific item."""
        query = """
        SELECT
            creators.firstName,
            creators.lastName,
            itemCreators.orderIndex
        FROM itemCreators
        JOIN creators ON itemCreators.creatorID = creators.creatorID
        WHERE itemCreators.itemID = ?
        ORDER BY itemCreators.orderIndex;
        """
        cursor.execute(query, (item_id,))
        return [f"{first} {last}" for first, last, _ in cursor.fetchall()]

    def get_pdf_backlink(self, cursor: sqlite3.Cursor, item_id: int) -> Optional[str]:
        """Get links to the zotero item attachment"""
        query = """
        SELECT
            items.itemID,
            'zotero://select/library/items/' || child.key as zotero_uri
        FROM items
        JOIN itemTypes ON items.itemTypeID = itemTypes.itemTypeID
        JOIN itemAttachments ON items.itemID = itemAttachments.parentItemID
        JOIN items as child ON itemAttachments.itemID = child.itemID
        WHERE itemAttachments.contentType = 'application/pdf'
        AND items.itemID = ?
        """
        cursor.execute(query, (item_id,))
        result = cursor.fetchone()
        if result is None:
            return None
        _, link = result
        if cursor.fetchone() is not None:
            print(f"Warning: Multiple attachments found for item {item_id}. Only the first attachment link will be used.")
        return link

    def format_creator_string(self, authors: List[str]) -> str:
        """Returns last name of first author followed by 'et al.' if there are more authors."""
        if not authors:
            return "Unknown Author"

        if len(authors) == 1:
            return authors[0].split()[-1]  # Get last name

        return f"{authors[0].split()[-1]} et al."

    def format_item_date(self, date: Optional[str]) -> Optional[str]:
        """Format date in YYYY."""
        if not date:
            return None

        match = re.search(r"\d{4}", date)
        return match.group(0) if match else None

    def get_venue_string(self, paper: Paper) -> Optional[str]:
        """Get formatted venue string based on paper type."""
        if paper["type"] == "conferencePaper":
            if paper.get("series"):
                return paper["series"]
            if paper.get("conferenceName"):
                return (
                    paper["conferenceName"].split(":")[0]
                    if ":" in paper["conferenceName"]
                    else paper["conferenceName"]
                )
        elif paper["type"] == "journalArticle":
            return paper.get("publicationTitle")
        return None

    def get_zotero_items(self) -> List[Paper]:
        """
        Retrieve all academic papers from Zotero database with their metadata.

        Returns:
            List[Paper]: List of papers with their metadata
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
            WHERE itemTypes.typeName IN (
                'journalArticle', 'conferencePaper', 'prePrint',
                'report', 'thesis', 'book', 'bookSection'
            )
            AND items.itemID NOT IN (
                SELECT itemID FROM itemAttachments
            )
            ORDER BY items.itemID, fields.fieldName;
        """

        cursor.execute(query)
        results = cursor.fetchall()

        # Process results into a more usable format
        papers: Dict[int, Paper] = {}
        for item_id, key, type_name, field_name, value in results:
            if item_id not in papers:
                papers[item_id] = {
                    "key": key,
                    "type": type_name,
                    "tags": self.get_item_tags(cursor, item_id),
                    "authors": self.get_item_authors(cursor, item_id),
                    "backlink": self.get_pdf_backlink(cursor, item_id),
                }
            papers[item_id][field_name] = value

        conn.close()
        return list(papers.values())

    def create_markdown_file(self, paper: Paper) -> None:
        """Create a markdown file for a paper with metadata in YAML frontmatter."""
        title = paper.get("title", "Untitled Paper")
        safe_title = re.sub(r'[<>:"/\\|?*]', "-", title)

        # Create YAML frontmatter
        frontmatter = [
            "---",
            f'title: "{title}"',
            "type: academic-paper",
            f'year: {self.format_item_date(paper.get("date")) or "Unknown"}',
            f'authors: {json.dumps(paper["authors"])}',
            f'zotero-key: {paper["key"]}',
            f'accessed: {paper.get("accessDate", "")}',
        ]

        if paper["tags"]:
            frontmatter.append(f'tags: {json.dumps(paper["tags"])}')

        if paper["authors"]:
            frontmatter.append(
                f'creator: {self.format_creator_string(paper["authors"])}'
            )

        venue = self.get_venue_string(paper)
        if venue:
            frontmatter.append(f"venue: {venue}")

        frontmatter.append("---\n")

        content = [
            "## Abstract",
            f'{paper.get("abstractNote", "")}\n',
            "## Notes",
            "## References",
            f'- Zotero Key: {paper["key"]}',
            f'- DOI: {paper.get("DOI", "")}',

            f'- [PDF]({paper["backlink"]})',
        ]

        file_path = self.papers_folder / f"{safe_title}.md"
        file_path.write_text("\n".join(frontmatter + content), encoding="utf-8")

    def sync(self) -> None:
        """Synchronize Zotero library with Obsidian vault."""
        papers = self.get_zotero_items()
        for paper in papers:
            self.create_markdown_file(paper)
        print(f"Synchronized {len(papers)} papers to Obsidian vault")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync Zotero library with Obsidian vault."
    )
    parser.add_argument(
        "--zotero-db",
        type=str,
        default="~/Zotero/zotero.sqlite",
        help="Path to Zotero SQLite database",
    )
    parser.add_argument(
        "--obsidian-vault",
        type=str,
        default="~/Documents/ObsidianVault",
        help="Path to Obsidian vault",
    )

    args = parser.parse_args()

    syncer = ZoteroObsidianSync(
        os.path.expanduser(args.zotero_db), os.path.expanduser(args.obsidian_vault)
    )
    syncer.sync()


if __name__ == "__main__":
    main()
