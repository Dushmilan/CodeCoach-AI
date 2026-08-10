import { MetadataRoute } from "next";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://codecoach.ai";

  // Static pages
  const staticPages: MetadataRoute.Sitemap = [
    {
      url: baseUrl,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 1,
    },
    {
      url: `${baseUrl}/problems`,
      lastModified: new Date(),
      changeFrequency: "daily",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/learn`,
      lastModified: new Date(),
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${baseUrl}/login`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.5,
    },
    {
      url: `${baseUrl}/register`,
      lastModified: new Date(),
      changeFrequency: "monthly",
      priority: 0.5,
    },
  ];

  // Dynamic question pages
  let questionPages: MetadataRoute.Sitemap = [];
  try {
    const questionsRes = await fetch(`${baseUrl}/api/questions`, {
      cache: "no-store",
    });
    if (questionsRes.ok) {
      const questions = (await questionsRes.json()) as { id: string }[];
      questionPages = questions.map((q: { id: string }) => ({
        url: `${baseUrl}/problems/${q.id}`,
        lastModified: new Date(),
        changeFrequency: "weekly" as const,
        priority: 0.7,
      }));
    }
  } catch (error) {
    console.error("Failed to fetch questions for sitemap:", error);
  }

  // Dynamic course pages
  let coursePages: MetadataRoute.Sitemap = [];
  try {
    const coursesRes = await fetch(`${baseUrl}/api/courses`, {
      cache: "no-store",
    });
    if (coursesRes.ok) {
      const courses = (await coursesRes.json()) as { id: string }[];
      coursePages = courses.map((c: { id: string }) => ({
        url: `${baseUrl}/learn/${c.id}`,
        lastModified: new Date(),
        changeFrequency: "weekly" as const,
        priority: 0.8,
      }));
    }
  } catch (error) {
    console.error("Failed to fetch courses for sitemap:", error);
  }

  return [...staticPages, ...questionPages, ...coursePages];
}
