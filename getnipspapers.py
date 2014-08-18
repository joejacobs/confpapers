import urllib
import cPickle as pickle
import os

# Extract the author and title information, PDF and abstract for all papers on
# a given the NIPS conference index page

# start config
protocol = "http"
domain = "papers.nips.cc"
index_uri = "http://papers.nips.cc/book/advances-in-neural-information-processing-systems-26-2013"
pdf_dir = "nips26offline/content/"
abstracts_dir = "abstracts/"
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

def get_pdf(uri, output_file):

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

if __name__ == "__main__":

    if not os.path.exists(pdf_dir):

        os.makedirs(pdf_dir)

    if not os.path.exists(abstracts_dir):

        os.makedirs(abstracts_dir)

    out_dict = {}
    fp = urllib.urlopen(index_uri)
    lines = fp.readlines()
    fp.close()

    for l in lines:

        idx = l.find("<a href=\"/paper/")

        if idx > 0:

            substr = l[idx+9:]
            idx = substr.find("\"")
            uri = "%s://%s%s" % (protocol, domain, substr[:idx])
            paper_id = int( substr[ 7:substr.find("-") ] )

            print "Processing Paper #%d" % paper_id

            pp = get_uri(uri)
            line = pp.readline()

            while line:

                idx = line.find("<meta name=\"citation_pdf_url\" content=\"")
                is_abstract = line.find("<p class=\"abstract\">")

                if idx >= 0:

                    substr = line[idx+39:]
                    idx = substr.find("\"")
                    pdf_uri = substr[:idx]
                    bib_uri = pdf_uri.replace(".pdf", "/bibtex")
                    filename = pdf_uri[ pdf_uri.find("/paper/")+7: ]
                    bp = get_uri(bib_uri)

                    line = bp.readline()
                    author = None
                    title = None

                    while line:

                        is_title = line.find("title = {")
                        is_author = line.find("author = {")

                        if is_author == 0:

                            author = line[ line.find("{")+1:line.find("},") ]
                        elif is_title == 0:

                            title = line[ line.find("{")+1:line.find("},") ]

                        line = bp.readline()

                    bp.close()
                    assert author and title

                    out_dict[paper_id] = (title, author)

                    if not os.path.isfile(pdf_dir + filename):

                        get_pdf(pdf_uri, pdf_dir + filename)

                elif is_abstract >= 0:

                    abstract = line[ is_abstract+20:line.find("</p>") ]
                    f = open(abstracts_dir + ("a%d.txt" % paper_id), "w")
                    f.write(abstract);
                    f.close()

                line = pp.readline()

            pp.close()
            
    pickle.dump( out_dict, open("papers.p", "wb") )
