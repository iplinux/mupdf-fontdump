#include <fitz.h>
#include <mupdf.h>

int showtree = 0;

void usage()
{
	fprintf(stderr, "usage: pdfrip [-d] [-p password] file.pdf [pages...]\n");
	exit(1);
}

/*
 * Draw page
 */

void showpage(pdf_xref *xref, fz_obj *pageobj)
{
	fz_error *error;
	pdf_page *page;

	fz_debugobj(pageobj);
	printf("\n");

	error = pdf_loadpage(&page, xref, pageobj);
	if (error)
		fz_abort(error);

	if (showtree)
	{
		printf("page\n");
		printf("  mediabox [ %g %g %g %g ]\n",
			page->mediabox.min.x, page->mediabox.min.y,
			page->mediabox.max.x, page->mediabox.max.y);
		printf("  rotate %d\n", page->rotate);

		printf("  resources\n");
		fz_debugobj(page->resources);
		printf("\n");

		printf("tree\n");
		fz_debugtree(page->tree);
		printf("endtree\n");
	}

	{
		fz_pixmap *pix;
		fz_renderer *gc;
		fz_matrix ctm;
		fz_rect bbox;

		error = fz_newrenderer(&gc, pdf_devicergb);
		if (error) fz_abort(error);

		ctm = fz_concat(fz_translate(0, -page->mediabox.max.y), fz_scale(1.0, -1.0));
printf("ctm %g %g %g %g %g %g\n",
	ctm.a, ctm.b, ctm.c, ctm.d, ctm.e, ctm.f);

printf("bounding!\n");
		bbox = fz_boundtree(page->tree, ctm);
printf("  [%g %g %g %g]\n", bbox.min.x, bbox.min.y, bbox.max.x, bbox.max.y);
printf("rendering!\n");
		error = fz_rendertree(&pix, gc, page->tree, ctm, page->mediabox);
		//error = fz_rendertree(&pix, gc, page->tree, ctm, bbox);
		if (error) fz_abort(error);
printf("done!\n");

		fz_debugpixmap(pix);
		fz_freepixmap(pix);

		fz_freerenderer(gc);
	}
}

int main(int argc, char **argv)
{
	fz_error *error;
	char *filename;
	pdf_xref *xref;
	pdf_pagetree *pages;
	int c;

	char *password = "";

	while ((c = getopt(argc, argv, "dp:")) != -1)
	{
		switch (c)
		{
		case 'p': password = optarg; break;
		case 'd': ++showtree; break;
		default: usage();
		}
	}

	if (argc - optind == 0)
		usage();

	filename = argv[optind++];

	error = pdf_openpdf(&xref, filename);
	if (error)
		fz_abort(error);

	error = pdf_decryptpdf(xref);
	if (error)
		fz_abort(error);

	if (xref->crypt)
	{
		error = pdf_setpassword(xref->crypt, password);
		if (error) fz_abort(error);
	}

	error = pdf_loadpagetree(&pages, xref);
	if (error) fz_abort(error);

	if (optind == argc)
	{
		printf("pagetree\n");
		pdf_debugpagetree(pages);
		printf("\n");
	}

	for ( ; optind < argc; optind++)
	{
		int page = atoi(argv[optind]);
		if (page < 1 || page > pdf_getpagecount(pages))
			fprintf(stderr, "page out of bounds: %d\n", page);
		printf("page %d\n", page);
		showpage(xref, pdf_getpageobject(pages, page - 1));
	}

	pdf_closepdf(xref);

	return 0;
}
