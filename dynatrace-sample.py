import dynatrace

def executeQuery(query):
	with dynatrace.sensor():
		print ("Executing query %s" % query)
		return "hello"

def handleRequest(url):
	with dynatrace.start_purepath():
		print ("Handling request %s" % url)
		for x in range(0, 3):
			executeQuery ("SELECT * FROM my_tbl WHERE id=%d" % (x))

dynatrace.init()
		
handleRequest('index.html')
