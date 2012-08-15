package de.astaro.gossip.data;

/*
 * Representation of a host, containing database id and host address.
 */
public class Host implements Comparable<Host>{
	private long id;
	private String address;
	
	public long getId(){
		return id;
	}
	
	public void setId(long id){
		this.id = id;
	}
	
	public String getAddress(){
		return address;
	}
	
	public void setAddress(String address){
		this.address = address;
	}
	
	@Override 
	public String toString(){
		return address; 
	}

	public int compareTo(Host another) {
		return address.compareTo(another.getAddress());
	}
}
