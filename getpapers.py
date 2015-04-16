import urllib
import cPickle as pickle
import os

# Extract the author and title information, PDF and abstract for all papers on
# a given the NIPS conference index page

# start config
protocol = "http"
domain = "papers.nips.cc"
index_uri = "http://papers.nips.cc/book/advances-in-neural-information-processing-systems-26-2013"
pdf_dir = "nips26offline/pdf/"
abstracts_dir = "nips26offline/abstracts/"
paper_details_file = "nips26offline/papers.p"
author_to_paper_file = "nips26offline/author_to_paper.p"
coauthors_file = "nips26offline/coauthors.p"
# end config

def get_uri(uri):

    tried = 0
    done = False
    fp = None

    while tried < 3 and not done:

        try:

            fp = urllib.urlopen(uri)
            done = True
        except:

            tried += 1
            print "%s: Try %d failed" % (uri, tried)

    if not done:

        raise

    return fp

def get_file(uri):

    fp = get_uri(uri)
    content = fp.readlines()
    fp.close()

    return content

def save_pdf(uri, output_file):

    tried = 0
    done = False

    while tried < 3 and not done:

        try:

            urllib.urlretrieve(uri, output_file)
            done = True
        except IOError:

            tried += 1
            print "%s: Try %d failed" % (pdf_uri, tried)

        if not done:

            raise

def parse_bibtex(bibtex):

    title = None
    authors = None

    # go through each line of bibtex and extract title and authors
    for line in bibtex:

        is_title = line.find("title = {")
        is_author = line.find("author = {")

        if is_author == 0:

            authors = line[ line.find("{")+1:line.find("},") ]
        elif is_title == 0:

            title = line[ line.find("{")+1:line.find("},") ]

    assert title and authors

    # split authors string to a list of authors
    authors = authors.split(' and ')

    return title, authors

def parse_nips_paper_html(html):

    abstract = None
    bib_uri = None
    pdf_uri = None
    pdf_filename = None

    for line in html:

        idx = line.find("<meta name=\"citation_pdf_url\" content=\"")
        is_abstract = line.find("<p class=\"abstract\">")

        if idx >= 0:

            substr = line[idx+39:]
            idx = substr.find("\"")
            pdf_uri = substr[:idx]
            bib_uri = pdf_uri.replace(".pdf", "/bibtex")
            pdf_filename = pdf_uri[ pdf_uri.find("/paper/")+7: ]

        elif is_abstract >= 0:

            abstract = line[ is_abstract+20:line.find("</p>") ]

    return abstract, bib_uri, pdf_uri, pdf_filename

def get_nips_paper_details(uri):

    abstract = None
    title = None
    authors = None
    pdf_uri = None
    pdf_filename = None

    # parse details from html
    paper_html = get_file(uri)
    abstract, bib_uri, pdf_uri, pdf_filename = parse_nips_paper_html(paper_html)

    # parse details from bibtex
    bibtex = get_file(bib_uri)
    title, authors = parse_bibtex(bibtex)

    return title, authors, abstract, pdf_uri, pdf_filename

def parse_nips_index(html, protocol, domain):

    paper_details_uri = {}

    for line in html:

        idx = line.find("<a href=\"/paper/")

        if idx > 0:

            substr = line[idx+9:]
            idx = substr.find("\"")
            uri = "%s://%s%s" % (protocol, domain, substr[:idx])
            paper_id = int( substr[ 7:substr.find("-") ] )

            paper_details_uri[paper_id] = uri

    return paper_details_uri

def get_nips_papers(index_uri, protocol, domain):

    nips_index = get_file(index_uri)
    paper_details_uri = parse_nips_index(nips_index, protocol, domain)
    paper_details = {}

    for paper_id in paper_details_uri.keys():

        print "get_nips_papers(): Paper #%d" % paper_id

        uri = paper_details_uri[paper_id]
        title, authors, abstract, pdf_uri, pdf_filename = get_nips_paper_details(uri)

        paper_details[paper_id] = (title, authors, abstract, pdf_uri, pdf_filename)

    return paper_details

if __name__ == "__main__":

    if not os.path.exists(pdf_dir):

        os.makedirs(pdf_dir)

    if not os.path.exists(abstracts_dir):

        os.makedirs(abstracts_dir)

    author_to_paper = {}
    coauthors = {}
    paper_details = get_nips_papers(index_uri, protocol, domain)

    for paper_id in paper_details.keys():

        print "Processing Paper #%d" % paper_id

        title, authors, abstract, pdf_uri, pdf_filename = paper_details[paper_id]

        # store author bibliography and coauthor details
        for author in authors:

            try:

                author_to_paper[author].append(paper_id)
            except KeyError:

                author_to_paper[author] = [paper_id]
                coauthors[author] = {}

            for author2 in authors:

                try:

                    coauthors[author][author2] += 1
                except KeyError:

                    coauthors[author][author2] = 1

        # store pdf
        if not os.path.isfile(pdf_dir + pdf_filename):

            save_pdf(pdf_uri, pdf_dir + pdf_filename)

        # store abstract
        f = open(abstracts_dir + ("%d.txt" % paper_id), "w")
        f.write(abstract);
        f.close()
            
    pickle.dump( paper_details, open(paper_details_file, "wb") )
    pickle.dump( author_to_paper, open(author_to_paper_file, "wb") )
    pickle.dump( coauthors_file, open(coauthors_file, "wb") )
