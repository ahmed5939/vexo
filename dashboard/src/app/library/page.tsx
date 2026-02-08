import { getLibrary } from '@/lib/db';
import LibraryPageClient from './LibraryPageClient';

export const dynamic = 'force-dynamic';

interface LibraryItem {
    id: number;
    title: string;
    artist_name: string;
    genre: string | null;
    contributors: string | null;
    sources: string | null;
    last_added: string;
}

export default async function LibraryPage() {
    let library: LibraryItem[] = [];

    try {
        library = (await getLibrary(500) as unknown) as LibraryItem[];
    } catch (error) {
        console.error('Failed to fetch library:', error);
    }

    return <LibraryPageClient initialLibrary={library} />;
}
